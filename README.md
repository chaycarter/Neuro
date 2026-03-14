# Neuro
Reccy Carter ecosystem — [neuro.reccy.dev](https://neuro.reccy.dev) | [cartersciences.com](https://www.cartersciences.com)

## Neuro Agent

An AI-powered desktop agent that sits on top of your screen and automates LinkedIn recruitment tasks on your open browser tabs.

**Powered by Claude (Anthropic) + Playwright**

### What it does

- Floats as an always-on-top overlay panel on your desktop
- Connects to your existing Chrome browser session (no new login needed)
- Understands plain English instructions: *"Find neurotech engineers in London and send connection requests"*
- Automates LinkedIn: search candidates, send personalised messages, connect, scrape profiles, read inbox
- Writes messages that sound like you — personalised, human, never generic

### Quick start

```bash
cd neuro-agent
bash setup.sh

# Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# Start Chrome with debugging port
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome

# Log into LinkedIn in that Chrome window, then:
source .venv/bin/activate
python main.py
```

### Example tasks you can give it

- `Search for BCI engineers with 5+ years experience in London`
- `Send a personalised connection request to the profile I have open`
- `Read my LinkedIn messages and summarise who needs a reply`
- `Find ML researchers at neurotech startups and draft outreach messages`
- `Scrape this profile and save their details`

### Project structure

```
neuro-agent/
├── main.py          # Entry point — wires UI + browser + agent
├── overlay.py       # Floating desktop UI (CustomTkinter)
├── agent.py         # Claude AI brain — plans and orchestrates actions
├── browser.py       # Playwright browser controller (CDP)
├── tasks/
│   └── linkedin.py  # LinkedIn task templates and message recipes
├── setup.sh         # One-command setup
├── requirements.txt
└── .env.example
```

### Note on LinkedIn Terms of Service

LinkedIn's ToS restricts automated access. This tool is built for semi-supervised use — you control what runs and when. For high-volume or fully automated workflows, consider LinkedIn's official [Recruiter API](https://developer.linkedin.com/product-catalog/recruiter).
