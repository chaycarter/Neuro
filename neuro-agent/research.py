"""
W — Chay Carter's Personal Assistant
Research module: pulls neurotech news, ArXiv papers, and compiles newsletter digests.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import xml.etree.ElementTree as ET

import httpx

# -----------------------------------------------------------------------
# Neurotech RSS / feed sources
# -----------------------------------------------------------------------
FEEDS = {
    "arxiv_ne":   "https://arxiv.org/rss/cs.NE",          # Neural & Evolutionary Computing
    "arxiv_nc":   "https://arxiv.org/rss/q-bio.NC",        # Neurons & Cognition
    "arxiv_sp":   "https://arxiv.org/rss/eess.SP",         # Signal Processing (BCI-adjacent)
    "nature_neuro": "https://www.nature.com/neuro.rss",    # Nature Neuroscience
    "nature_bt":  "https://www.nature.com/nbt.rss",        # Nature Biotechnology
    "ieee":       "https://spectrum.ieee.org/feeds/topic/biomedical.rss",
    "mit_tr":     "https://www.technologyreview.com/feed/",
}

# Key neurotech companies / orgs to watch in headlines
NEUROTECH_KEYWORDS = [
    "brain-computer interface", "BCI", "neural interface", "neurotech", "neurotechnology",
    "brain implant", "neural prosthetic", "EEG", "MEG", "electrocorticography", "ECoG",
    "deep brain stimulation", "DBS", "transcranial", "TMS", "tDCS",
    "Neuralink", "Synchron", "Blackrock Neurotech", "Paradromics", "Kernel",
    "CTRL-labs", "Emotiv", "Nuro", "Openwater", "BrainGate", "NeuroTechX",
    "neural decoding", "neuroprosthetics", "closed-loop", "spike sorting",
    "cortical", "neuromorphic", "spiking neural", "optogenetics",
    "neurofeedback", "brain atlas", "connectome", "synaptic",
]


@dataclass
class Article:
    title: str
    url: str
    summary: str
    source: str
    published: str
    category: str = "general"
    relevance_score: int = 0


@dataclass
class NewsletterDraft:
    date: str
    top_papers: list[Article]
    industry_news: list[Article]
    company_updates: list[Article]
    raw_markdown: str = ""


class NeuroResearcher:
    """Fetches and filters neurotech content for Chay's newsletter."""

    def __init__(self, log_callback=None):
        self.log = log_callback or (lambda msg, level="info": print(f"[{level}] {msg}"))

    # ------------------------------------------------------------------
    # Feed fetching
    # ------------------------------------------------------------------
    async def fetch_feed(self, name: str, url: str, days_back: int = 7) -> list[Article]:
        """Fetch and parse an RSS feed, returning recent neurotech articles."""
        articles = []
        cutoff = datetime.now() - timedelta(days=days_back)

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
                if resp.status_code != 200:
                    self.log(f"Feed {name}: HTTP {resp.status_code}", "warning")
                    return []
        except Exception as e:
            self.log(f"Feed {name} error: {e}", "warning")
            return []

        try:
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            # Handle both RSS and Atom
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)

            for item in items[:20]:
                title_el = item.find("title") or item.find("atom:title", ns)
                link_el = item.find("link") or item.find("atom:link", ns)
                desc_el = item.find("description") or item.find("atom:summary", ns)
                pub_el = item.find("pubDate") or item.find("atom:published", ns) or item.find("atom:updated", ns)

                title = title_el.text if title_el is not None else ""
                link = (link_el.text or link_el.get("href", "")) if link_el is not None else ""
                desc = desc_el.text if desc_el is not None else ""
                pub = pub_el.text if pub_el is not None else ""

                if not title or not link:
                    continue

                # Score relevance
                combined = (title + " " + desc).lower()
                score = sum(1 for kw in NEUROTECH_KEYWORDS if kw.lower() in combined)

                if score > 0 or name.startswith("arxiv"):
                    articles.append(Article(
                        title=title.strip(),
                        url=link.strip(),
                        summary=self._clean_html(desc[:400]) if desc else "",
                        source=name,
                        published=pub,
                        relevance_score=score,
                    ))
        except ET.ParseError as e:
            self.log(f"Feed {name} parse error: {e}", "warning")

        # Sort by relevance
        articles.sort(key=lambda a: a.relevance_score, reverse=True)
        return articles[:10]

    def _clean_html(self, text: str) -> str:
        import re
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Full research run
    # ------------------------------------------------------------------
    async def run_research(self, days_back: int = 7) -> NewsletterDraft:
        """Pull all feeds and compile into a draft."""
        self.log("Starting neurotech research sweep...", "agent")

        tasks = [self.fetch_feed(name, url, days_back) for name, url in FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles: list[Article] = []
        for res in results:
            if isinstance(res, list):
                all_articles.extend(res)

        self.log(f"Fetched {len(all_articles)} relevant articles.", "success")

        # Categorise
        papers = [a for a in all_articles if a.source.startswith("arxiv") or "nature" in a.source]
        papers = sorted(papers, key=lambda a: a.relevance_score, reverse=True)[:8]

        company_keywords = [k.lower() for k in [
            "Neuralink", "Synchron", "Blackrock", "Paradromics", "Kernel", "CTRL-labs", "Emotiv"
        ]]
        company_news = [
            a for a in all_articles
            if any(k in (a.title + a.summary).lower() for k in company_keywords)
        ][:5]

        industry = [
            a for a in all_articles
            if a not in papers and a not in company_news
        ][:6]

        draft = NewsletterDraft(
            date=datetime.now().strftime("%Y-%m-%d"),
            top_papers=papers,
            industry_news=industry,
            company_updates=company_news,
        )
        draft.raw_markdown = self._compile_markdown(draft)
        return draft

    def _compile_markdown(self, draft: NewsletterDraft) -> str:
        lines = [
            f"# Neurotech Weekly Digest — {draft.date}",
            f"> Compiled by W for Chay Carter | neuro.reccy.dev\n",
        ]

        if draft.top_papers:
            lines.append("## Research Highlights\n")
            for a in draft.top_papers:
                lines.append(f"**[{a.title}]({a.url})**")
                if a.summary:
                    lines.append(f"> {a.summary[:200]}...\n")
                else:
                    lines.append("")

        if draft.company_updates:
            lines.append("## Company Updates\n")
            for a in draft.company_updates:
                lines.append(f"- **[{a.title}]({a.url})** *({a.source})*")

        if draft.industry_news:
            lines.append("\n## Industry & Ecosystem\n")
            for a in draft.industry_news:
                lines.append(f"- **[{a.title}]({a.url})** *({a.source})*")

        lines.append("\n---")
        lines.append("_Curated for the Neuro Ecosystem — Carter Sciences_")
        return "\n".join(lines)

    def save_draft(self, draft: NewsletterDraft, output_dir: str = "data/newsletter_drafts"):
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"neuro_digest_{draft.date}.md")
        with open(path, "w") as f:
            f.write(draft.raw_markdown)
        return path
