"""
W — Chay Carter's Personal Assistant
Carter Sciences / Reccy Neuro / neuro.reccy.dev

Usage:
  1. Start Chrome with debugging port:
       google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome

  2. Log into LinkedIn in that Chrome window.

  3. Run W:
       python main.py

  Set ANTHROPIC_API_KEY in .env (copy .env.example).
  Optionally set GOOGLE_SHEET_ID + GOOGLE_CREDENTIALS_PATH for spreadsheet access.
"""

import asyncio
import queue
import threading
import os

from dotenv import load_dotenv
load_dotenv()

from overlay import WOverlay
from browser import BrowserController
from agent import WAgent
from sheets import SheetsManager


CDP_URL = os.getenv("CDP_URL", "http://localhost:9222")


class WApp:
    def __init__(self):
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.browser = BrowserController(cdp_url=CDP_URL)
        self.sheets = SheetsManager(log_callback=self.log)
        self.agent: WAgent | None = None
        self._running = True

    def log(self, message: str, level: str = "info", done: bool = False):
        self.result_queue.put({"message": message, "level": level, "done": done})

    # ------------------------------------------------------------------
    # Async worker thread
    # ------------------------------------------------------------------
    def _run_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_main())

    async def _async_main(self):
        self.log("W starting up...", "agent")

        # Connect to browser
        connected = await self.browser.connect()
        if connected:
            self.log("Connected to Chrome.", "success")
        else:
            self.log(
                f"Chrome not found at {CDP_URL}.\n"
                "  Start it with: google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome",
                "warning",
            )

        self.agent = WAgent(
            browser_executor=self.browser.execute,
            research_runner=None,       # research handled inside agent
            sheets_manager=self.sheets,
            result_callback=self.log,
        )

        self.log("Ready. What do you need, Chay?", "success")

        while self._running:
            try:
                task = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._get_task(timeout=0.1)
                )
                if task is None:
                    continue

                task_type = task.get("type", "")

                if task_type == "stop":
                    if self.agent:
                        self.agent.stop()
                    continue

                if task_type == "natural_language":
                    instruction = task.get("instruction", "")
                    try:
                        await self.agent.run_task(instruction)
                    except Exception as e:
                        self.log(f"Error: {e}", "error")
                    self.log("", "info", done=True)

            except Exception as e:
                self.log(f"Worker error: {e}", "error")

        await self.browser.disconnect()

    def _get_task(self, timeout: float):
        try:
            return self.task_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def run(self):
        worker = threading.Thread(target=self._run_async_loop, daemon=True)
        worker.start()

        ui = WOverlay(task_queue=self.task_queue, result_queue=self.result_queue)
        ui.mainloop()

        self._running = False


if __name__ == "__main__":
    app = WApp()
    app.run()
