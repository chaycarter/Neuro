"""
W — LinkedIn task templates
Message recipes written in Chay Carter's voice.

Style rules (hard):
- No em dashes
- No bold in body text
- No AI language: no "delve", "leverage", "cutting-edge", "transformative", "robust", "seamless"
- British spelling
- Short sentences. Direct. Warm but not gushing.
- No generic openers ("I hope this finds you well")
- Connection notes: under 300 characters, specific to the person, no ask, no pitch
"""

from dataclasses import dataclass, field


@dataclass
class CandidateSearch:
    role: str
    location: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    connection_degree: str = "2nd"

    def to_instruction(self) -> str:
        skill_str = ", ".join(self.skills) if self.skills else ""
        exp_str = f" with {self.experience_years}+ years experience" if self.experience_years else ""
        loc_str = f" in {self.location}" if self.location else ""
        skill_clause = f" skilled in {skill_str}" if skill_str else ""
        return (
            f"Search LinkedIn for {self.role} candidates{skill_clause}{exp_str}{loc_str} "
            f"({self.connection_degree} connections preferred). "
            f"Extract name, headline, company, and profile URL for the top 10 results."
        )


@dataclass
class ConnectionOutreach:
    context: str = "neurotech"

    def to_instruction(self) -> str:
        return (
            "On the current LinkedIn profile, read the person's name, current role, company, and about section. "
            "Send a connection request from Chay Carter (Founder, Carter Sciences / Reccy Neuro). "
            "The note must: reference something specific from their actual profile, be under 300 characters, "
            "feel like it was written by a person not a tool. No pitch. No ask. No em dashes. British spelling."
        )


@dataclass
class MessageCampaign:
    campaign_goal: str

    def to_instruction(self) -> str:
        return (
            "On the current LinkedIn profile tab, read the person's full name, role, company, and background. "
            "Open a message to them and write a personalised message from Chay Carter. "
            f"Goal: {self.campaign_goal}. "
            "Rules: sound like Chay (casual, direct, no corporate speak). Under 150 words. "
            "Reference something specific from their profile. No em dashes. British spelling. "
            "No AI language. Then send the message."
        )


@dataclass
class ProfileScrape:
    def to_instruction(self) -> str:
        return (
            "On the current LinkedIn profile page, extract all available information: "
            "full name, headline, location, about section, current and past roles, "
            "education, skills, and any contact info shown. "
            "Return a structured summary."
        )


@dataclass
class InboxManager:
    action: str = "summarise"

    def to_instruction(self) -> str:
        if self.action == "reply_pending":
            return (
                "Open LinkedIn messages. Find any unanswered messages from candidates, founders, or researchers. "
                "Draft a brief reply from Chay Carter in his voice: direct, warm, no corporate language. "
                "No em dashes. British spelling."
            )
        return (
            "Open LinkedIn messages. Summarise the last 10 conversations: "
            "who sent them, what they're about, and which need a reply."
        )


# -----------------------------------------------------------------------
# Message templates — Chay's voice
# Placeholders: {name}, {company}, {role}, {specific_detail}, {sector}, {skill}
# -----------------------------------------------------------------------
MESSAGE_TEMPLATES = {
    "cold_outreach": (
        "Hi {name}, came across your work in {specific_detail} and genuinely impressed. "
        "Building the neurotech talent network at Reccy Neuro and think you'd be a great addition. "
        "Would love to connect. Chay"
    ),
    "job_opportunity": (
        "Hi {name}, working with a {sector} company looking for someone with your background in {skill}. "
        "Interesting role, happy to share more if you're open to a conversation. "
        "Chay Carter, Carter Sciences"
    ),
    "follow_up": (
        "Hi {name}, just following up. No rush at all. "
        "I'll keep you in mind for roles in the neurotech space regardless. Best, Chay"
    ),
    "network_build": (
        "Hi {name}, your work at {company} on {specific_detail} is exactly what "
        "we cover at Reccy Neuro. Would love to connect and learn more. Chay"
    ),
    "newsletter_invite": (
        "Hi {name}, I run The Neurotech Newsletter on Substack covering research, companies and the market. "
        "Think it might be relevant to your work. Happy to share the link if useful. Chay"
    ),
    "interview_request": (
        "Hi {name}, I do a monthly interview series on cartersciences.com featuring founders and researchers "
        "building in neurotech. Would love to feature your work on {specific_detail}. "
        "No sales, no agenda, just a good conversation. Chay"
    ),
}
