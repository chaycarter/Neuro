"""
Neuro Agent - Claude AI Brain
Interprets natural language instructions and orchestrates browser tasks.
"""

import asyncio
import json
import os
from typing import Any, Callable

import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are Neuro, an AI recruitment assistant for Carter Sciences and neuro.reccy.dev.
You help Chay Carter automate LinkedIn recruitment tasks: searching for candidates,
sending personalised messages, connecting with people, and gathering profile data.

You control a real browser. When given a task, break it into precise browser actions.
Always write messages that sound human, warm, and specific — never generic or spammy.
Personalise outreach using the candidate's actual name, role, and company.

You respond with a JSON array of actions. Each action has:
  { "action": "<action_name>", "params": { ... }, "description": "<what you're doing>" }

Available actions:
- navigate_to_tab       { "url_contains": "linkedin.com/in" }  — focus a tab matching URL
- get_current_url       {}                                      — read current URL
- get_page_text         {}                                      — extract visible text
- get_profile_data      {}                                      — extract LinkedIn profile fields
- type_text             { "selector": "...", "text": "..." }    — type into a field
- click_element         { "selector": "...", "description": "..." }
- search_linkedin       { "query": "...", "filters": {...} }    — run a LinkedIn people search
- send_connection_req   { "note": "..." }                       — send connection request with note
- send_message          { "recipient_name": "...", "message": "..." }
- scroll_page           { "direction": "down", "amount": 500 }
- wait                  { "ms": 800 }                          — natural pause
- read_messages         {}                                      — read unread LinkedIn messages
- get_open_tabs         {}                                      — list all open browser tabs
- done                  { "summary": "..." }                    — task complete

Rules:
1. Always start by understanding which tab to use (get_open_tabs or navigate_to_tab).
2. Use get_profile_data before sending any message — personalise with real details.
3. Add wait actions between interactions (600–1500ms) for natural pacing.
4. Messages must sound like they are from Chay Carter, founder of Carter Sciences.
5. Respond ONLY with a valid JSON array of actions — no prose, no markdown code fences.
"""


class NeuroAgent:
    def __init__(self, browser_executor: Callable, result_callback: Callable):
        """
        browser_executor: async callable(action_dict) -> result_dict
        result_callback: sync callable(message, level) — sends log lines to UI
        """
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.execute = browser_executor
        self.log = result_callback
        self._stop_flag = False
        self.conversation_history: list[dict] = []

    def stop(self):
        self._stop_flag = True

    async def run_task(self, instruction: str):
        """Main entry point: given a natural-language instruction, plan and execute."""
        self._stop_flag = False
        self.log(f"Planning task: {instruction}", "agent")

        # First, get a snapshot of open tabs to give the agent context
        tabs = await self.execute({"action": "get_open_tabs", "params": {}})

        context = f"""Current browser tabs:
{json.dumps(tabs, indent=2)}

User instruction: {instruction}

Respond with a JSON array of actions to complete this task."""

        self.conversation_history.append({"role": "user", "content": context})

        max_iterations = 10
        for iteration in range(max_iterations):
            if self._stop_flag:
                self.log("Stopped.", "warning")
                return

            # Call Claude
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
            )

            raw = response.content[0].text.strip()

            # Parse actions
            try:
                actions = json.loads(raw)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                match = re.search(r'\[.*\]', raw, re.DOTALL)
                if match:
                    actions = json.loads(match.group())
                else:
                    self.log(f"Could not parse agent response: {raw[:200]}", "error")
                    return

            self.conversation_history.append({"role": "assistant", "content": raw})

            # Execute each action
            action_results = []
            for action in actions:
                if self._stop_flag:
                    break

                action_name = action.get("action", "")
                description = action.get("description", action_name)
                params = action.get("params", {})

                self.log(f"→ {description}", "info")

                if action_name == "done":
                    self.log(action.get("params", {}).get("summary", "Task complete."), "success")
                    return

                result = await self.execute({"action": action_name, "params": params})
                action_results.append({"action": action_name, "result": result})

                # Natural pacing between actions
                if action_name != "wait":
                    await asyncio.sleep(0.3)

            # Feed results back for next iteration if not done
            if not any(a.get("action") == "done" for a in actions):
                feedback = f"Action results:\n{json.dumps(action_results, indent=2)}\n\nContinue or respond with a 'done' action if complete."
                self.conversation_history.append({"role": "user", "content": feedback})

        self.log("Max iterations reached. Task ended.", "warning")
