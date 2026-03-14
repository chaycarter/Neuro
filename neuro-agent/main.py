"""
Neuro Agent - Main Entry Point
Carter Sciences / neuro.reccy.dev

Usage:
  1. Start Chrome with debugging port:
       google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome

  2. Log into LinkedIn in that Chrome window.

  3. Run the agent:
       python main.py

  Optional: set ANTHROPIC_API_KEY in a .env file (copy .env.example).
"""

import asyncio
import queue
import threading
import sys
import os

from dotenv import load_dotenv
load_dotenv()

from overlay import NeuroOverlay
from browser import BrowserController
from agent import NeuroAgent


CDP_URL = os.getenv("CDP_URL", "http://localhost:9222")


class NeuroApp:
    def __init__(self):
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.browser = BrowserController(cdp_url=CDP_URL)
        self.agent: NeuroAgent | None = None
        self._running = True

    # ------------------------------------------------------------------
    # Log helper (thread-safe: posts to result_queue → UI)
    # ------------------------------------------------------------------
    def log(self, message: str, level: str = "info", done: bool = False):
        self.result_queue.put({"message": message, "level": level, "done": done})

    # ------------------------------------------------------------------
    # Async worker (runs in a background thread)
    # ------------------------------------------------------------------
    def _run_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_main())

    async def _async_main(self):
        # Connect to browser
        self.log("Connecting to Chrome...", "info")
        connected = await self.browser.connect()
        if connected:
            self.log("Connected to Chrome. Ready.", "success")
        else:
            self.log(
                f"Could not connect to Chrome at {CDP_URL}.\n"
                "Start Chrome with: google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome",
                "warning",
            )

        self.agent = NeuroAgent(
            browser_executor=self.browser.execute,
            result_callback=self.log,
        )

        # Task loop
        while self._running:
            try:
                # Non-blocking check every 0.1s
                task = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._task_queue_get(timeout=0.1)
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

    def _task_queue_get(self, timeout: float):
        try:
            return self.task_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def run(self):
        # Start async worker in background thread
        worker = threading.Thread(target=self._run_async_loop, daemon=True)
        worker.start()

        # Run the UI on the main thread (required by Tkinter)
        ui = NeuroOverlay(
            task_queue=self.task_queue,
            result_queue=self.result_queue,
        )
        ui.mainloop()

        # Cleanup
        self._running = False


if __name__ == "__main__":
    app = NeuroApp()
    app.run()
