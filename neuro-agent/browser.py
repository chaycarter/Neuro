"""
W — Browser Automation Layer
Connects to an existing Chrome session via CDP and executes actions.

Usage:
  1. Launch Chrome with remote debugging:
     google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome

  2. Log into LinkedIn in that window, then start W.
"""

import asyncio
import json
import random
import re
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


# Human-like typing: randomised delay between keystrokes
TYPING_DELAY_MS = (60, 140)
# Pause range between actions (ms) — feels natural
ACTION_PAUSE_MS = (400, 900)


class BrowserController:
    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser: Browser | None = None
        self._current_page: Page | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    async def connect(self) -> bool:
        """Connect to an already-running Chrome session."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            return True
        except Exception as e:
            return False

    async def disconnect(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _get_page(self, url_contains: str = "") -> Page | None:
        """Return the first tab whose URL contains the given string."""
        if not self.browser:
            return None
        for context in self.browser.contexts:
            for page in context.pages:
                if url_contains.lower() in page.url.lower():
                    return page
        # Fall back to first page
        contexts = self.browser.contexts
        if contexts and contexts[0].pages:
            return contexts[0].pages[0]
        return None

    # ------------------------------------------------------------------
    # Core action dispatcher
    # ------------------------------------------------------------------
    async def execute(self, action_dict: dict) -> Any:
        action = action_dict.get("action", "")
        params = action_dict.get("params", {})

        handlers = {
            "get_open_tabs": self._get_open_tabs,
            "navigate_to_tab": self._navigate_to_tab,
            "get_current_url": self._get_current_url,
            "get_page_text": self._get_page_text,
            "get_profile_data": self._get_profile_data,
            "type_text": self._type_text,
            "click_element": self._click_element,
            "search_linkedin": self._search_linkedin,
            "send_connection_req": self._send_connection_req,
            "send_message": self._send_message,
            "scroll_page": self._scroll_page,
            "audit_connections": self._audit_connections,
            "remove_connection": self._remove_connection,
            "read_followers": self._read_followers,
            "wait": self._wait,
            "read_messages": self._read_messages,
        }

        handler = handlers.get(action)
        if not handler:
            return {"error": f"Unknown action: {action}"}

        try:
            return await handler(params)
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------
    async def _get_open_tabs(self, params: dict) -> list:
        if not self.browser:
            return []
        tabs = []
        for ctx in self.browser.contexts:
            for page in ctx.pages:
                tabs.append({"title": await page.title(), "url": page.url})
        return tabs

    async def _navigate_to_tab(self, params: dict) -> dict:
        url_contains = params.get("url_contains", "")
        page = await self._get_page(url_contains)
        if page:
            self._current_page = page
            await page.bring_to_front()
            return {"url": page.url, "title": await page.title()}
        return {"error": f"No tab found matching: {url_contains}"}

    async def _get_current_url(self, params: dict) -> dict:
        page = self._current_page or await self._get_page()
        if not page:
            return {"error": "No page available"}
        return {"url": page.url}

    async def _get_page_text(self, params: dict) -> dict:
        page = self._current_page or await self._get_page()
        if not page:
            return {"error": "No page available"}
        text = await page.inner_text("body")
        # Trim to avoid huge context
        return {"text": text[:4000]}

    async def _get_profile_data(self, params: dict) -> dict:
        """Extract structured data from a LinkedIn profile page."""
        page = self._current_page or await self._get_page("linkedin.com/in/")
        if not page:
            return {"error": "No LinkedIn profile tab found"}

        await page.wait_for_load_state("domcontentloaded")

        try:
            data = await page.evaluate("""() => {
                const get = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? el.innerText.trim() : null;
                };
                const getAll = (sel) => {
                    return Array.from(document.querySelectorAll(sel))
                        .map(el => el.innerText.trim())
                        .filter(Boolean);
                };

                return {
                    name: get('h1.text-heading-xlarge') || get('h1'),
                    headline: get('.text-body-medium.break-words'),
                    location: get('.text-body-small.inline.t-black--light.break-words'),
                    about: get('#about ~ .display-flex .full-width'),
                    current_role: get('.experience-item .t-bold span[aria-hidden="true"]'),
                    current_company: get('.experience-item .t-14.t-normal span[aria-hidden="true"]'),
                    skills: getAll('.skill-categories-skills__name span[aria-hidden="true"]').slice(0,10),
                    url: window.location.href,
                };
            }""")
            return data
        except Exception as e:
            # Fallback: return page text
            text = await page.inner_text("body")
            return {"raw_text": text[:3000], "error": str(e)}

    async def _type_text(self, params: dict) -> dict:
        page = self._current_page or await self._get_page()
        if not page:
            return {"error": "No page"}
        selector = params.get("selector", "")
        text = params.get("text", "")
        try:
            await page.click(selector)
            await asyncio.sleep(random.uniform(0.2, 0.5))
            # Human-like typing
            for char in text:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(*TYPING_DELAY_MS) / 1000)
            return {"typed": len(text)}
        except Exception as e:
            return {"error": str(e)}

    async def _click_element(self, params: dict) -> dict:
        page = self._current_page or await self._get_page()
        if not page:
            return {"error": "No page"}
        selector = params.get("selector", "")
        try:
            await page.click(selector)
            await asyncio.sleep(random.uniform(*ACTION_PAUSE_MS) / 1000)
            return {"clicked": selector}
        except Exception as e:
            return {"error": str(e)}

    async def _search_linkedin(self, params: dict) -> dict:
        """Navigate to a LinkedIn people search."""
        query = params.get("query", "")
        filters = params.get("filters", {})
        page = await self._get_page("linkedin.com")
        if not page:
            return {"error": "No LinkedIn tab open"}

        self._current_page = page
        await page.bring_to_front()

        encoded = query.replace(" ", "%20")
        url = f"https://www.linkedin.com/search/results/people/?keywords={encoded}"

        # Apply basic filters
        if filters.get("connection") == "2nd":
            url += "&network=%5B%22S%22%5D"
        if filters.get("location"):
            loc = filters["location"].replace(" ", "%20")
            url += f"&geoUrn=%5B%22{loc}%22%5D"

        await page.goto(url)
        await page.wait_for_load_state("networkidle", timeout=10000)
        await asyncio.sleep(random.uniform(0.8, 1.5))

        # Extract results
        results = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.reusable-search__result-container'))
                .slice(0, 10)
                .map(card => ({
                    name: card.querySelector('.entity-result__title-text a span[aria-hidden]')?.innerText?.trim(),
                    headline: card.querySelector('.entity-result__primary-subtitle')?.innerText?.trim(),
                    location: card.querySelector('.entity-result__secondary-subtitle')?.innerText?.trim(),
                    profile_url: card.querySelector('.app-aware-link')?.href,
                }));
        }""")
        return {"results": results, "count": len(results)}

    async def _send_connection_req(self, params: dict) -> dict:
        """Send a LinkedIn connection request on the current profile page."""
        note = params.get("note", "")
        page = self._current_page or await self._get_page("linkedin.com/in/")
        if not page:
            return {"error": "No profile page open"}

        try:
            # Click Connect button
            connect_btn = page.locator(
                'button:has-text("Connect"), button[aria-label*="Connect"]'
            ).first
            await connect_btn.click()
            await asyncio.sleep(random.uniform(0.6, 1.0))

            if note:
                # Click "Add a note"
                add_note = page.locator('button:has-text("Add a note")').first
                await add_note.click()
                await asyncio.sleep(0.4)

                note_field = page.locator('textarea[name="message"]').first
                await note_field.click()
                for char in note:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(*TYPING_DELAY_MS) / 1000)

            # Send
            send_btn = page.locator('button:has-text("Send"), button[aria-label="Send now"]').first
            await send_btn.click()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            return {"sent": True, "note_length": len(note)}
        except Exception as e:
            return {"error": str(e)}

    async def _send_message(self, params: dict) -> dict:
        """Send a LinkedIn message to an open conversation."""
        message = params.get("message", "")
        page = self._current_page or await self._get_page("linkedin.com")
        if not page:
            return {"error": "No LinkedIn tab open"}

        try:
            # Find message compose box
            msg_box = page.locator(
                '.msg-form__contenteditable, div[role="textbox"][aria-label*="message"]'
            ).first
            await msg_box.click()
            await asyncio.sleep(random.uniform(0.3, 0.7))

            for char in message:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(*TYPING_DELAY_MS) / 1000)

            await asyncio.sleep(random.uniform(0.5, 1.0))
            # Send with Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(random.uniform(0.6, 1.2))
            return {"sent": True, "message_length": len(message)}
        except Exception as e:
            return {"error": str(e)}

    async def _scroll_page(self, params: dict) -> dict:
        page = self._current_page or await self._get_page()
        if not page:
            return {"error": "No page"}
        direction = params.get("direction", "down")
        amount = params.get("amount", 500)
        delta = amount if direction == "down" else -amount
        await page.mouse.wheel(0, delta)
        await asyncio.sleep(random.uniform(0.3, 0.6))
        return {"scrolled": delta}

    async def _wait(self, params: dict) -> dict:
        ms = params.get("ms", 800)
        # Add small randomness for naturalness
        actual = ms + random.randint(-100, 200)
        await asyncio.sleep(max(actual, 100) / 1000)
        return {"waited_ms": actual}

    async def _read_messages(self, params: dict) -> dict:
        """Navigate to LinkedIn messages and extract unread conversations."""
        page = await self._get_page("linkedin.com")
        if not page:
            return {"error": "No LinkedIn tab open"}
        self._current_page = page

        await page.goto("https://www.linkedin.com/messaging/")
        await page.wait_for_load_state("networkidle", timeout=10000)

        messages = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.msg-conversation-listitem'))
                .slice(0, 10)
                .map(item => ({
                    name: item.querySelector('.msg-conversation-listitem__participant-names')?.innerText?.trim(),
                    preview: item.querySelector('.msg-conversation-listitem__message-snippet')?.innerText?.trim(),
                    time: item.querySelector('time')?.innerText?.trim(),
                    unread: item.classList.contains('msg-conversation-listitem--unread-thread'),
                }));
        }""")
        return {"messages": messages, "count": len(messages)}

    async def _audit_connections(self, params: dict) -> dict:
        """Scrape connections list and return data for scoring."""
        page = await self._get_page("linkedin.com")
        if not page:
            return {"error": "No LinkedIn tab open"}
        self._current_page = page

        await page.goto("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        await page.wait_for_load_state("networkidle", timeout=12000)
        await asyncio.sleep(random.uniform(1.0, 1.8))

        # Scroll to load more
        for _ in range(3):
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(random.uniform(0.6, 1.0))

        connections = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.mn-connection-card'))
                .slice(0, 60)
                .map(card => ({
                    name: card.querySelector('.mn-connection-card__name')?.innerText?.trim(),
                    headline: card.querySelector('.mn-connection-card__occupation')?.innerText?.trim(),
                    profile_url: card.querySelector('a.mn-connection-card__link')?.href,
                }));
        }""")
        return {"connections": connections, "count": len(connections)}

    async def _remove_connection(self, params: dict) -> dict:
        """Remove connection on currently open profile page."""
        page = self._current_page or await self._get_page("linkedin.com/in/")
        if not page:
            return {"error": "No profile page open"}
        try:
            # Click the More (…) button
            more_btn = page.locator('button[aria-label*="More actions"]').first
            await more_btn.click()
            await asyncio.sleep(random.uniform(0.5, 0.9))
            # Click Remove connection
            remove = page.locator('span:has-text("Remove connection")').first
            await remove.click()
            await asyncio.sleep(0.4)
            # Confirm
            confirm = page.locator('button:has-text("Remove")').first
            await confirm.click()
            await asyncio.sleep(random.uniform(0.6, 1.0))
            return {"removed": True}
        except Exception as e:
            return {"error": str(e)}

    async def _read_followers(self, params: dict) -> dict:
        """Extract followers from Chay's profile followers tab."""
        page = await self._get_page("linkedin.com")
        if not page:
            return {"error": "No LinkedIn tab open"}
        self._current_page = page

        await page.goto("https://www.linkedin.com/in/chay-carter/followers/")
        await page.wait_for_load_state("networkidle", timeout=12000)
        await asyncio.sleep(random.uniform(1.0, 1.5))

        followers = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.follows-recommendation-card'))
                .slice(0, 30)
                .map(card => ({
                    name: card.querySelector('.follows-recommendation-card__name')?.innerText?.trim(),
                    headline: card.querySelector('.follows-recommendation-card__occupation')?.innerText?.trim(),
                    profile_url: card.querySelector('a')?.href,
                }));
        }""")

        # Fallback: try generic people cards
        if not followers:
            followers = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('.entity-result__item'))
                    .slice(0, 30)
                    .map(card => ({
                        name: card.querySelector('.entity-result__title-text a span[aria-hidden]')?.innerText?.trim(),
                        headline: card.querySelector('.entity-result__primary-subtitle')?.innerText?.trim(),
                        profile_url: card.querySelector('.app-aware-link')?.href,
                    }));
            }""")

        return {"followers": followers, "count": len(followers)}
