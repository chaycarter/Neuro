"""
W — Chay Carter's Personal Assistant
AI brain: interprets instructions, plans actions, orchestrates browser + research + spreadsheet tasks.
"""

import asyncio
import json
import os
import re
from typing import Any, Callable

import anthropic
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------
# W's full identity and deep context
# -----------------------------------------------------------------------
SYSTEM_PROMPT = """You are W — the personal AI assistant to Chay Carter.

## Who Chay is

Chay Carter. Founder of Carter Sciences, co-founder of Reccy Neuro. Based in Mexico City.
20 years specialist recruitment across trading technology, energy/infrastructure, and life sciences.
Now fully focused on neurotech. Not a scientist — a recruiter and operator with a commercial lens on a technical market.

**Carter Sciences** — specialist neurotech headhunting and advisory. Contingent, contract, and executive search.
Also home to 1:1 Career Advisory and W/Werk (AI recruitment assistant, in development with Donte Hobbs).

**Reccy Neuro** (co-founded with Max Kelly) — neurotech job board and market intelligence platform.
Always positioned as intelligence, not just a job board. Feeds leads into Carter Sciences.

**The Neuro Newsletter / Substack** — theneurotechnewsletter.substack.com — weekly, monetised.
Also a separate bi-weekly newsletter (~1,000 subscribers), monetised.
Monthly interview articles on cartersciences.com — credibility and lead gen, not monetised.
Regular LinkedIn content (personal + Reccy Neuro accounts).
Medium / NeurotechX contribution monthly.
Podcast appearances — opinion leadership positioning.

**Chay's contact:** chay@cartersciences.com | cartersciences.com | linkedin.com/in/chay-carter/

## Chay's voice and tone

Casual but punchy. Professional without being corporate. Conversational. Direct.
Talks about neurotech from the market, not from a lab or lecture hall.
Short sentences preferred. British/English spelling.
First person for all Chay-authored content.

STRICT style rules — always apply to any content you write as Chay:
- No em dashes
- No bold in body text (headers only)
- No AI language: never use "delve", "leverage", "cutting-edge", "transformative", "robust", "seamless"
- British spelling: colour, organise, specialise, recognised, etc.
- No generic openers ("I hope this finds you well", "I wanted to reach out")
- Connection notes: specific, warm, under 300 characters, no ask, no pitch

## What Chay cares about

- The patient population — what neurotech does for real people
- Commercial realities of building in a regulated, capital-intensive market
- The people building neurotech and what it takes to hire them
- Ecosystem building: intelligence + media + headhunting under one roof
- BCIs, neuromodulation, closed-loop systems — the 10-20 year vision

## Network building strategy

Target connections: founders, CTOs, VPs, Directors, Professors, Research Directors at neurotech companies and labs.
Key companies: Neuralink, Synchron, Blackrock Neurotech, Paradromics, Kernel, CTRL-labs, Emotiv, Precision Neuroscience, Science Corporation, Openwater, Nalu Medical, Axoft, Arc Institute, Allen Institute, BrainGate, NeuroTechX.
Remove: spam, unrelated industries (forex, MLM, real estate, solar panels, generic marketing).
Master spreadsheet: shared Google Sheet with Max Kelly tracking targets, status, notes.

## Available actions

{ "action": "<name>", "params": { ... }, "description": "<what you're doing>" }

Browser:
- get_open_tabs          {}
- navigate_to_tab        { "url_contains": "..." }
- get_current_url        {}
- get_page_text          {}
- get_profile_data       {}
- type_text              { "selector": "...", "text": "..." }
- click_element          { "selector": "...", "description": "..." }
- scroll_page            { "direction": "down|up", "amount": 500 }
- wait                   { "ms": 800 }

LinkedIn:
- search_linkedin        { "query": "...", "filters": { "connection": "2nd", "location": "..." } }
- send_connection_req    { "note": "..." }
- send_message           { "recipient_name": "...", "message": "..." }
- read_messages          {}
- audit_connections      {}
- remove_connection      {}
- read_followers         {}

Research:
- run_research           { "days_back": 7 }
- save_newsletter        {}

Spreadsheet:
- sheet_get_targets      { "status": "target" }
- sheet_update_status    { "linkedin_url": "...", "status": "...", "notes": "..." }
- sheet_add_record       { "name": "...", "linkedin_url": "...", "company": "...", "role": "...", "seniority": "...", "status": "target", "notes": "..." }
- sheet_summary          {}

Done:
- done                   { "summary": "..." }

## Rules

1. Always call get_open_tabs first unless the tab context is clear.
2. Before sending any message or connection request: call get_profile_data to personalise.
3. Add wait (600-1500ms) between interactions for natural pacing.
4. All written content must follow Chay's strict style rules above.
5. Connection notes must be under 300 characters, specific to the person, no ask.
6. Auditing: flag non-neurotech as "review", clear spam as "remove", neurotech senior as "prioritise".
7. Show spreadsheet summary before acting on it.
8. Respond ONLY with a valid JSON array of actions. No prose. No markdown fences.
"""


class WAgent:
    """W — Chay Carter's personal AI assistant."""

    def __init__(
        self,
        browser_executor: Callable,
        research_runner: Callable,
        sheets_manager: Any,
        result_callback: Callable,
    ):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.browser = browser_executor
        self.research = research_runner
        self.sheets = sheets_manager
        self.log = result_callback
        self._stop_flag = False
        self.conversation_history: list[dict] = []
        self._newsletter_draft = None

    def stop(self):
        self._stop_flag = True

    def reset_conversation(self):
        self.conversation_history = []

    # ------------------------------------------------------------------
    # Main task runner
    # ------------------------------------------------------------------
    async def run_task(self, instruction: str):
        self._stop_flag = False
        self.log(f"W on it: {instruction}", "agent")

        tabs = await self.browser({"action": "get_open_tabs", "params": {}})
        sheet_summary = self.sheets.export_summary() if self.sheets else {}

        context = f"""Open browser tabs:
{json.dumps(tabs, indent=2)}

Master spreadsheet summary:
{json.dumps(sheet_summary, indent=2)}

Task from Chay: {instruction}

Plan and return a JSON array of actions."""

        self.conversation_history.append({"role": "user", "content": context})

        for _iteration in range(12):
            if self._stop_flag:
                self.log("Stopped.", "warning")
                return

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
            )

            raw = response.content[0].text.strip()

            try:
                actions = json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r'\[.*\]', raw, re.DOTALL)
                if match:
                    try:
                        actions = json.loads(match.group())
                    except json.JSONDecodeError:
                        self.log(f"Could not parse plan: {raw[:200]}", "error")
                        return
                else:
                    self.log(f"Could not parse plan: {raw[:200]}", "error")
                    return

            self.conversation_history.append({"role": "assistant", "content": raw})

            action_results = []
            for action in actions:
                if self._stop_flag:
                    break

                name = action.get("action", "")
                desc = action.get("description", name)
                params = action.get("params", {})

                self.log(f"→ {desc}", "info")

                if name == "done":
                    self.log(params.get("summary", "Done."), "success")
                    return

                result = await self._dispatch(name, params)
                action_results.append({"action": name, "result": result})

                if name != "wait":
                    await asyncio.sleep(0.3)

            if not any(a.get("action") == "done" for a in actions):
                feedback = (
                    f"Results:\n{json.dumps(action_results, indent=2)}\n\n"
                    "Continue or use 'done' if complete."
                )
                self.conversation_history.append({"role": "user", "content": feedback})

        self.log("Reached iteration limit.", "warning")

    # ------------------------------------------------------------------
    # Action dispatcher
    # ------------------------------------------------------------------
    async def _dispatch(self, action: str, params: dict) -> Any:
        if action == "run_research":
            return await self._run_research(params)
        if action == "save_newsletter":
            return await self._save_newsletter(params)

        if action == "sheet_get_targets":
            records = self.sheets.get_targets(params.get("status", "target"))
            return [
                {"name": r.name, "url": r.linkedin_url, "company": r.company,
                 "role": r.role, "seniority": r.seniority, "notes": r.notes}
                for r in records[:20]
            ]
        if action == "sheet_update_status":
            self.sheets.update_status(
                params.get("linkedin_url", ""),
                params.get("status", "contacted"),
                params.get("notes", ""),
            )
            return {"updated": True}
        if action == "sheet_add_record":
            from sheets import ConnectionRecord
            fields = ConnectionRecord.__dataclass_fields__
            rec = ConnectionRecord(**{k: v for k, v in params.items() if k in fields})
            self.sheets.add_record(rec)
            return {"added": rec.name}
        if action == "sheet_summary":
            return self.sheets.export_summary()

        # All other actions go to browser
        return await self.browser({"action": action, "params": params})

    # ------------------------------------------------------------------
    # Research helpers
    # ------------------------------------------------------------------
    async def _run_research(self, params: dict) -> dict:
        try:
            from research import NeuroResearcher
            researcher = NeuroResearcher(log_callback=self.log)
            draft = await researcher.run_research(days_back=params.get("days_back", 7))
            self._newsletter_draft = draft
            return {
                "papers": len(draft.top_papers),
                "company_updates": len(draft.company_updates),
                "industry_news": len(draft.industry_news),
                "preview": draft.raw_markdown[:600],
            }
        except Exception as e:
            return {"error": str(e)}

    async def _save_newsletter(self, params: dict) -> dict:
        if not self._newsletter_draft:
            return {"error": "No draft — run run_research first"}
        try:
            from research import NeuroResearcher
            path = NeuroResearcher(log_callback=self.log).save_draft(self._newsletter_draft)
            return {"saved": path}
        except Exception as e:
            return {"error": str(e)}
