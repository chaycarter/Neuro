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

Carter Sciences: specialist neurotech headhunting and advisory. Contingent, contract, executive search.
Also home to 1:1 Career Advisory and W/Werk (AI recruitment assistant, in development with Donte Hobbs).

Reccy Neuro (co-founded with Max Kelly): neurotech job board and MARKET DATA/INTELLIGENCE platform.
CRITICAL: always position Reccy as intelligence, not just a jobs board.

The Neuro Newsletter / Substack: theneurotechnewsletter.substack.com, weekly, monetised.
Separate bi-weekly newsletter (~1,000 subscribers), monetised.
Monthly interview articles on cartersciences.com — credibility and lead gen.
Regular LinkedIn content (personal + Reccy Neuro accounts).
Medium / NeurotechX monthly. Podcast appearances for opinion leadership.

Chay's contact: chay@cartersciences.com | cartersciences.com | linkedin.com/in/chay-carter/

## Content skill — APPLY TO ALL WRITTEN OUTPUT

### Voice
Casual but punchy. Professional without being corporate. Conversational. Direct. Confident without arrogance.
Talks about neurotech from the market, not from a lab or lecture hall.
Short sentences. British/English spelling. First person for all Chay-authored content.

### STRICT style rules — never break these
- No em dashes. Ever. Use commas, full stops, or restructure.
- No bold in body text. Headers only.
- BANNED words/phrases: "delve", "it's worth noting", "in the realm of", "leverage" (as verb),
  "cutting-edge", "game-changer", "transformative", "exciting", "thrilled", "passionate about",
  "robust", "seamless", "at the end of the day", "in today's fast-paced world"
- No generic openers: "I hope this finds you well", "I wanted to reach out", "Please don't hesitate"
- No vague superlatives: "incredibly", "truly", "really"
- No passive voice where active is possible
- No long rambling intros — get to the point fast
- Never claim "first" or "world's leading" without evidence

### Content formats

LinkedIn personal (Carter Sciences) wrap-up post:
- Max 150-200 words. Bullet-style or short paragraphs.
- Covers: placements, articles published, Reccy updates, market moves.
- Ends with CTA or reflective closing line. 3-5 hashtags max.

LinkedIn Reccy Neuro role post:
- Lead with market context (why this role matters now).
- 2-3 short paragraphs. End with link/CTA to Reccy.
- Position Reccy as intelligence platform.

Carter Sciences interview article:
- Prose intro (2-4 sentences). Attribution: "Interview by Chay Carter".
- Bold question headers ONLY (no other bold). First-person answers in subject's voice.
- Pull quote (italicised, standalone, 1-2 per interview). 1,000-1,800 words.
- Intro style example: "[Name] has spent the better part of [X] years doing [Y].
  As [role] at [company], they're now the person [founders/teams/clients] call when [specific situation]."

Substack article:
- 600-1,200 words. No listicle format — flowing prose.
- Chay as informed insider, not just reporter. Offers perspective.
- Covers: funding news, tech trends, hiring signals, company moves.

Newsletter (bi-weekly):
- More detailed than Substack. Can include Reccy market data.

Neurotech glossary for accurate references:
BCI, DBS, SCS, VNS, TMS, tDCS, EEG, fNIRS, MEA, FES, RNS, HNS, PNS, FUS.

### Content sources
Neurotech funding (Crunchbase, LinkedIn), Reccy job data, FDA clearances,
conferences (NeurotechX, BCI Society), Neurotech Master Hiring Map (516 companies).

## Network building strategy

Target: founders, CTOs, VPs, Directors, Professors, Research Directors at neurotech companies and labs.
Key companies: Neuralink, Synchron, Blackrock Neurotech, Paradromics, Kernel, CTRL-labs, Emotiv,
Precision Neuroscience, Science Corporation, Openwater, Nalu Medical, Axoft, Arc Institute,
Allen Institute, BrainGate, NeuroTechX.
Remove: spam, unrelated industries (forex, MLM, real estate, solar panels, generic marketing).
Master spreadsheet: shared Google Sheet with Max Kelly tracking targets, status, notes.

## What Chay cares about

- The patient population and what neurotech does for real people
- Commercial realities of building in regulated, capital-intensive markets
- The people building neurotech and what it takes to hire them
- Ecosystem building: intelligence + media + headhunting under one roof
- BCIs, neuromodulation, closed-loop systems — the 10-20 year vision

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

Content (write and save drafts — ALL output must follow Chay's strict style rules):
- draft_linkedin_post    { "type": "weekly_wrap|role_post", "context": "..." }
  Weekly wrap: 150-200 words, bullet/short paragraphs, 3-5 hashtags, CTA.
  Role post: lead with market context, 2-3 paras, position Reccy as intelligence platform.
- draft_substack         { "topic": "...", "angle": "...", "sources": [...] }
  600-1,200 words, flowing prose, Chay as informed insider, not just reporter.
- draft_interview_intro  { "subject_name": "...", "subject_role": "...", "subject_company": "...", "subject_expertise": "..." }
  2-4 sentence prose intro + attribution line. Get into it fast. No "delighted to".
- draft_newsletter_ed    { "highlights": [...], "market_intel": "..." }
  Bi-weekly, more detailed than Substack. Can include Reccy data.
- save_content_draft     { "filename": "...", "content": "..." }
  Save any draft to data/content_drafts/.

Market Intelligence (Reccy Neuro lens — intelligence first, not just jobs):
- intel_company          { "company": "..." }
  Technology, stage, funding, headcount, hiring signals, leadership, BD relevance.
- intel_vertical         { "vertical": "..." }
  Top 5-8 companies, recent funding/M&A, hiring signals, FDA news, content angle.
- intel_funding_scan     { "min_usd_m": 5, "days_back": 30 }
  Neurotech funding rounds above threshold — company, amount, round, lead investor.
- intel_hiring_signals   { "query": "..." }
  Who's hiring in neurotech right now, ordered by commercial relevance to Carter Sciences.
- intel_weekly_briefing  {}
  5-7 notable neurotech things this week, ordered by relevance to Chay's flywheel.

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
4. ALL written content must follow Chay's strict style rules. Check for banned words before returning.
5. Connection notes: under 300 characters, specific to the person, no ask.
6. Auditing: flag non-neurotech as "review", clear spam as "remove", neurotech senior as "prioritise".
7. Show spreadsheet summary before acting on it.
8. Founder lens: for any strategy/BD question, filter through commercial impact + flywheel effect.
9. Never position Reccy Neuro as "just a job board".
10. Respond ONLY with a valid JSON array of actions. No prose. No markdown fences.
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

        # Content drafting actions
        if action in ("draft_linkedin_post", "draft_substack", "draft_interview_intro",
                      "draft_newsletter_ed", "save_content_draft"):
            return await self._draft_content(action, params)

        # Market intelligence actions
        if action.startswith("intel_"):
            return await self._market_intel(action, params)

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

    # ------------------------------------------------------------------
    # Content drafting — uses a second Claude call with the content skill
    # ------------------------------------------------------------------
    async def _draft_content(self, action: str, params: dict) -> dict:
        """
        Calls Claude specifically for content generation, enforcing
        Chay's strict voice and style rules from the content skill.
        """
        os.makedirs("data/content_drafts", exist_ok=True)

        if action == "save_content_draft":
            filename = params.get("filename", "draft.md")
            content = params.get("content", "")
            path = os.path.join("data/content_drafts", filename)
            with open(path, "w") as f:
                f.write(content)
            self.log(f"Saved draft: {path}", "success")
            return {"saved": path}

        # Build a targeted content prompt
        prompts = {
            "draft_linkedin_post": self._linkedin_post_prompt,
            "draft_substack":      self._substack_prompt,
            "draft_interview_intro": self._interview_intro_prompt,
            "draft_newsletter_ed": self._newsletter_ed_prompt,
        }
        prompt_fn = prompts.get(action)
        if not prompt_fn:
            return {"error": f"Unknown content action: {action}"}

        user_prompt = prompt_fn(params)

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        draft = response.content[0].text.strip()
        self.log(f"Draft ready ({len(draft)} chars).", "success")
        return {"draft": draft, "length": len(draft)}

    def _linkedin_post_prompt(self, p: dict) -> str:
        post_type = p.get("type", "weekly_wrap")
        context = p.get("context", "")
        if post_type == "weekly_wrap":
            return (
                f"Write a LinkedIn wrap-up post for Chay Carter's personal feed (Carter Sciences). "
                f"Context for this week: {context}. "
                "Max 200 words. Bullet-style or short paragraphs. No headers. "
                "End with a CTA or reflective closing line. 3-5 hashtags only. "
                "Follow all voice rules strictly. Return just the post text."
            )
        return (
            f"Write a LinkedIn post for the Reccy Neuro feed highlighting a neurotech role. "
            f"Role/context: {context}. "
            "Lead with market context. 2-3 short paragraphs. "
            "Position Reccy as a market intelligence platform, not just a job board. "
            "End with a CTA linking to Reccy. Follow all voice rules. Return just the post text."
        )

    def _substack_prompt(self, p: dict) -> str:
        topic = p.get("topic", "")
        angle = p.get("angle", "")
        sources = p.get("sources", [])
        src_str = "\n".join(f"- {s}" for s in sources) if sources else "Use your knowledge."
        return (
            f"Write a Substack article for The Neurotech Newsletter (theneurotechnewsletter.substack.com). "
            f"Topic: {topic}. Angle/perspective: {angle}. "
            f"Sources/context:\n{src_str}\n\n"
            "600-1,200 words. Flowing prose, no listicles. "
            "Chay as an informed insider offering perspective, not just reporting. "
            "British spelling. Follow all voice rules strictly. Return just the article."
        )

    def _interview_intro_prompt(self, p: dict) -> str:
        name = p.get("subject_name", "")
        role = p.get("subject_role", "")
        company = p.get("subject_company", "")
        expertise = p.get("subject_expertise", "")
        return (
            f"Write the intro paragraph for a Carter Sciences interview article featuring {name}, "
            f"{role} at {company}. Their expertise: {expertise}. "
            "2-4 sentences. Set the scene, establish credibility, explain why they matter. "
            "Do NOT start with 'I'm delighted' or any variation. Get into it immediately. "
            "Follow the example style: '[Name] has spent [X] years doing [Y]. "
            "As [role] at [company], they're now the person [situation].'\n"
            "Then add: 'Interview by Chay Carter' on a new line. "
            "British spelling. Follow all voice rules. Return just the intro + attribution."
        )

    def _newsletter_ed_prompt(self, p: dict) -> str:
        highlights = p.get("highlights", [])
        market_intel = p.get("market_intel", "")
        hl_str = "\n".join(f"- {h}" for h in highlights) if highlights else ""
        return (
            "Write a bi-weekly newsletter edition for Chay Carter's separate newsletter (~1,000 subscribers). "
            f"Key highlights this edition:\n{hl_str}\n"
            f"Market intel from Reccy Neuro: {market_intel}\n\n"
            "More detailed than a Substack article. Can include data and market signals. "
            "British spelling. Follow all voice rules strictly. Return just the newsletter content."
        )

    # ------------------------------------------------------------------
    # Market intelligence — Reccy Neuro lens
    # ------------------------------------------------------------------
    async def _market_intel(self, action: str, params: dict) -> dict:
        """
        Generates structured market intelligence using Claude's knowledge
        + the Reccy Neuro intelligence framework.
        Intelligence is formatted for direct use in BD prep, content, or Reccy data.
        """
        intel_prompts = {
            "intel_company": lambda p: (
                f"Give Chay Carter a company deep-dive on: {p.get('company')}. "
                "Cover: technology/product, development stage, recent funding (amount, round, date, lead investor), "
                "key indications, headcount estimate and hiring signals, key leadership, "
                "notable recent news (FDA, trials, partnerships), and whether they are a "
                "Carter Sciences BD target or candidate source. "
                "Use the Reccy Neuro intelligence framework: data-driven, commercial lens. "
                "200-300 words max. British spelling."
            ),
            "intel_vertical": lambda p: (
                f"Give Chay Carter a vertical scan for the neurotech vertical: {p.get('vertical')}. "
                "Cover: top 5-8 active companies, recent funding or M&A, hiring signals, "
                "technology/regulatory developments, emerging players worth watching. "
                "End with a suggested content angle for Chay's Substack or LinkedIn. "
                "Reccy Neuro lens: intelligence first. British spelling."
            ),
            "intel_funding_scan": lambda p: (
                f"List recent neurotech funding rounds above ${p.get('min_usd_m', 5)}M "
                f"from the last {p.get('days_back', 30)} days. "
                "For each: company, amount, round type, lead investor, date, technology type, indication. "
                "Flag if any of these companies should be added to Carter Sciences BD targets. "
                "Use your knowledge up to August 2025."
            ),
            "intel_hiring_signals": lambda p: (
                f"Identify neurotech hiring signals based on: {p.get('query', 'general neurotech')}. "
                "Who is actively growing their teams? Which companies have multiple open roles? "
                "Which are scaling from research to commercial (strongest BD signal)? "
                "Order by relevance to Carter Sciences executive search and Reccy Neuro platform. "
                "Practical, usable output. British spelling."
            ),
            "intel_weekly_briefing": lambda p: (
                "Give Chay Carter a weekly neurotech briefing. "
                "5-7 notable things that happened in neurotech recently. "
                "Order by relevance to his flywheel: Carter Sciences BD, Reccy Neuro data, newsletter content. "
                "For each item: 1-2 sentences, why it matters to Chay specifically. "
                "British spelling. No em dashes."
            ),
        }

        prompt_fn = intel_prompts.get(action)
        if not prompt_fn:
            return {"error": f"Unknown intel action: {action}"}

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_fn(params)}],
        )
        intel = response.content[0].text.strip()
        self.log(f"Intel ready.", "success")
        return {"intel": intel}
