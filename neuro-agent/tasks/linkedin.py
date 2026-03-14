"""
Neuro Agent - LinkedIn Task Templates
Pre-built task recipes for common recruitment workflows.
These are passed as instructions to the AI agent.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CandidateSearch:
    """Search LinkedIn for candidates matching a role."""
    role: str
    location: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    connection_degree: str = "2nd"  # 1st, 2nd, 3rd

    def to_instruction(self) -> str:
        skill_str = ", ".join(self.skills) if self.skills else ""
        exp_str = f" with {self.experience_years}+ years experience" if self.experience_years else ""
        loc_str = f" in {self.location}" if self.location else ""
        conn_str = f" ({self.connection_degree} connections preferred)"
        skill_clause = f" skilled in {skill_str}" if skill_str else ""
        return (
            f"Search LinkedIn for {self.role} candidates{skill_clause}{exp_str}{loc_str}{conn_str}. "
            f"Extract their names, headlines, companies, and profile URLs. Return top 10 results."
        )


@dataclass
class ConnectionOutreach:
    """Send personalised connection requests."""
    sender_name: str = "Chay Carter"
    sender_company: str = "Carter Sciences"
    sender_role: str = "Founder"
    context: str = "neurotech recruitment"
    personalise: bool = True

    def to_instruction(self) -> str:
        return (
            f"On the current LinkedIn profile, extract the person's name, current role, and company. "
            f"Then send a connection request with a personalised note from {self.sender_name}, "
            f"{self.sender_role} at {self.sender_company}. "
            f"Reference their specific work in {self.context}. "
            f"Keep it under 300 characters, warm and authentic — never salesy."
        )


@dataclass
class MessageCampaign:
    """Send personalised messages to a list of profiles."""
    campaign_goal: str  # e.g. "invite to apply for BCI Engineer role at NeuroX"
    sender_name: str = "Chay Carter"
    sender_company: str = "Carter Sciences / neuro.reccy.dev"

    def to_instruction(self) -> str:
        return (
            f"On the current LinkedIn profile tab, read the person's name, role, and background. "
            f"Open a message to them and write a personalised message from {self.sender_name} at "
            f"{self.sender_company}. Goal: {self.campaign_goal}. "
            f"Sound like a real person, reference something specific from their profile. "
            f"Keep it under 150 words. Then send the message."
        )


@dataclass
class ProfileScrape:
    """Extract full structured data from a LinkedIn profile."""

    def to_instruction(self) -> str:
        return (
            "On the current LinkedIn profile page, extract all available information: "
            "full name, headline, location, about section, current and past roles, "
            "education, skills, and any contact info shown. "
            "Return a structured summary."
        )


@dataclass
class InboxManager:
    """Read and summarise LinkedIn messages."""
    action: str = "summarise"  # summarise | reply_pending

    def to_instruction(self) -> str:
        if self.action == "reply_pending":
            return (
                "Open LinkedIn messages. Find any unanswered messages from candidates or recruiters. "
                "Draft a brief, professional reply to each one from Chay Carter."
            )
        return (
            "Open LinkedIn messages. Summarise the last 10 conversations: "
            "who sent them, what they're about, and which ones need a reply."
        )


# -----------------------------------------------------------------------
# Message templates — used by the AI agent as starting points
# -----------------------------------------------------------------------
MESSAGE_TEMPLATES = {
    "cold_outreach": (
        "Hi {name}, I came across your work in {field} and was genuinely impressed "
        "by {specific_detail}. I'm building a neurotech talent network at neuro.reccy.dev "
        "and think you'd be a great fit. Would love to connect — Chay"
    ),
    "job_opportunity": (
        "Hi {name}, I'm working with a {company_type} in the {sector} space who are "
        "looking for someone with your background in {skill}. It's a {role_type} role. "
        "Happy to share more if you're open to a chat? — Chay Carter, Carter Sciences"
    ),
    "follow_up": (
        "Hi {name}, just following up on my previous message. "
        "If now isn't the right time, totally fine — I'll keep you in mind for future roles "
        "in the neurotech space. Best, Chay"
    ),
    "network_build": (
        "Hi {name}, your work at {company} in {area} is exactly the kind of thing "
        "we spotlight on neuro.reccy.dev. Would love to connect and learn more. — Chay"
    ),
}
