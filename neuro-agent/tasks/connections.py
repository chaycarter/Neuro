"""
W — Connection audit and management tasks.
Scores LinkedIn connections: who to keep, who to remove, who to target.
"""

from dataclasses import dataclass, field


# -----------------------------------------------------------------------
# Seniority signals — connections W should prioritise pursuing
# -----------------------------------------------------------------------
SENIOR_TITLE_SIGNALS = [
    "founder", "co-founder", "ceo", "cto", "coo", "cso", "chief",
    "vp ", "vice president", "svp", "evp",
    "director", "head of", "managing director", "general manager",
    "partner", "principal", "president",
    "professor", "phd", "research director", "chief scientist",
]

NEUROTECH_COMPANY_SIGNALS = [
    "neuralink", "synchron", "blackrock neurotech", "paradromics", "kernel",
    "ctrl-labs", "emotiv", "openwater", "braingate", "nuro", "nalu medical",
    "precision neuroscience", "science corporation", "medtronic neuro",
    "boston scientific neuro", "abbott neuromodulation",
    "neuros medical", "nalu", "axoft", "arc institute",
    "allen institute", "janelia", "howard hughes", "nih brain",
    "darpa", "wellcome", "gates foundation",
    "neurotech", "neural interface", "bci", "brain computer",
    "neuromodulation", "neurostimulation", "neuroprosthetics",
]

NEUROTECH_ROLE_SIGNALS = [
    "neuroscientist", "neuroengineer", "neural engineer",
    "bci researcher", "brain computer interface",
    "computational neuroscience", "systems neuroscience",
    "neural signal", "neural decoding", "spike sorting",
    "eeg", "ecog", "lfp", "electrophysiology",
    "optogenetics", "neuropixels",
    "neurotech", "neural implant", "neural prosthetic",
]

# Connections that are clearly off-topic — flag for review
WEAK_SIGNALS = [
    "real estate", "forex", "crypto trading", "mlm", "network marketing",
    "life coach", "wellness", "insurance agent", "mortgage",
    "solar panel", "marketing agency", "seo specialist",
]


@dataclass
class ConnectionScore:
    name: str
    headline: str
    profile_url: str
    score: int = 0               # 0–10
    seniority_match: bool = False
    neurotech_match: bool = False
    weak_signal: bool = False
    recommendation: str = "keep" # keep | remove | prioritise | connect


def score_connection(name: str, headline: str, company: str, profile_url: str) -> ConnectionScore:
    """Score a LinkedIn connection for neurotech relevance."""
    combined = (headline + " " + company).lower()
    score = 0

    neuro = any(sig in combined for sig in NEUROTECH_COMPANY_SIGNALS + NEUROTECH_ROLE_SIGNALS)
    senior = any(sig in combined for sig in SENIOR_TITLE_SIGNALS)
    weak = any(sig in combined for sig in WEAK_SIGNALS)

    if neuro:
        score += 5
    if senior:
        score += 3
    if weak:
        score -= 4

    # Bonus for clear neurotech + senior combo
    if neuro and senior:
        score += 2

    score = max(0, min(10, score))

    if weak and score <= 1:
        rec = "remove"
    elif score >= 7:
        rec = "prioritise"
    elif score >= 4:
        rec = "keep"
    else:
        rec = "review"

    return ConnectionScore(
        name=name,
        headline=headline,
        profile_url=profile_url,
        score=score,
        seniority_match=senior,
        neurotech_match=neuro,
        weak_signal=weak,
        recommendation=rec,
    )


@dataclass
class ConnectionAudit:
    """Full audit task — analyse existing connections page."""

    def to_instruction(self) -> str:
        return """
Navigate to https://www.linkedin.com/mynetwork/invite-connect/connections/
Scroll through your connections list and extract the first 50 connections:
name, headline, company, profile URL.
For each, assess whether they are relevant to neurotech/BCI/neural interface.
Return a JSON list of objects with: name, headline, company, profile_url.
"""


@dataclass
class RemoveConnection:
    """Remove a specific connection."""
    profile_url: str
    name: str

    def to_instruction(self) -> str:
        return f"""
Navigate to {self.profile_url}
Find the 'More' or connection options button.
Click 'Remove connection'. Confirm if prompted.
Do this gently — one connection at a time.
"""


@dataclass
class TargetedConnect:
    """Connect with a senior neurotech person from the master list."""
    name: str
    profile_url: str
    company: str
    role: str
    context_note: str = ""

    def to_instruction(self) -> str:
        return f"""
Navigate to {self.profile_url}
Read {self.name}'s full profile — their current role at {self.company}, recent posts, about section.
Send a connection request with a personalised note from Chay Carter (Founder, Carter Sciences / neuro.reccy.dev).
The note must:
- Reference something specific from their profile or recent work
- Mention Carter Sciences or neuro.reccy.dev naturally
- Be under 300 characters, warm and genuine
- Not be salesy or ask for anything
Extra context: {self.context_note}
"""


@dataclass
class FollowerAnalysis:
    """Analyse followers vs following to find senior people not yet connected."""

    def to_instruction(self) -> str:
        return """
Navigate to Chay's LinkedIn profile followers list.
Extract the top 30 followers: name, headline, company, profile URL.
Identify which ones are C-level/VP/Director at neurotech companies.
Return a prioritised list of who Chay should connect with next.
"""
