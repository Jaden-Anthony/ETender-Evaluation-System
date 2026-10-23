# ETender Evaluation System

A beginner-friendly Python project that scans live South African government tender opportunities and helps you spot only the ones relevant to AI, automation, digital marketing, and digital services.

This project was built to solve a real problem: public tender portals are noisy, and manually reviewing hundreds of notices is time-consuming. The system pulls data from the eTenders portal, filters for relevant keywords, evaluates tenders using a local AI model, and narrows the list down to genuine opportunities.

## What this project does

The app:

- fetches live tender listings from the South African eTenders website
- filters relevant tenders using AI and digital marketing keywords
- checks each result with a local Ollama AI model
- removes obvious false positives such as hardware, civil works, or unrelated supply contracts
- exports qualified tenders to CSV/JSON
- optionally sends a daily email digest or Windows notification

## Why this matters

Government tender portals often contain thousands of listings, but most are not relevant to digital work. This project helps a user quickly find tenders for:

- AI and machine learning
- automation and workflow systems
- digital marketing and advertising
- website and portal development
- branding and communications projects
- data and analytics work

This makes it useful for:

- founders building service businesses
- consultants tracking opportunities
- teams scouting high-value digital contracts
- developers who want to automate procurement discovery

## Project architecture

The project is organized into a small modular Python application.

- `main.py` - the main script you run
- `src/fetcher.py` - downloads the active tenders from the public portal
- `src/keyword_filter.py` - looks for relevant terms in the tender text
- `src/ai_evaluator.py` - uses Ollama to decide if a tender is truly relevant
- `src/pipeline.py` - runs the end-to-end workflow
- `src/exporter.py` - exports shortlisted tenders to files
- `src/notifier.py` - sends emails or Windows notifications
- `src/config.py` - project settings and keywords
- `src/models.py` - structured data models
- `tests/` - unit tests for project logic

## Who this is for

This project is especially useful for:

- non-technical business owners who want a better way to find relevant contracts
- developers creating AI-powered scraping workflows
- consultants working in digital services and marketing
- people learning Python + AI + automation through a real-world use case

## Beginner-friendly setup guide

If you are not technical, this section is written to be as simple as possible.

### 1) Install the tools you need

You need to install:

- Python 3.12 or later
- Git
- VS Code (recommended but optional)
- Ollama

#### Install Python

On Windows:

1. Go to https://www.python.org/downloads/
2. Download the latest Python 3.12 installer
3. Run the installer
4. Make sure you check the box that says: "Add Python to PATH"
5. Finish installation

To check whether it worked:

```bash
python --version
```

If that does not work, try:

```bash
py --version
```

#### Install Git

Download and install Git from:

https://git-scm.com/downloads

Then verify:

```bash
git --version
```

#### Install VS Code (recommended)

Download from:

https://code.visualstudio.com/

#### Install Ollama

Go to:

https://ollama.com/download

Install it and start the Ollama app. This is required because the project uses a local AI model to evaluate tenders.

After installing, open a terminal and run:

```bash
ollama --version
```

Then pull a model the project can use, for example:

```bash
ollama pull qwen2.5:14b
```

This may take a few minutes depending on your internet speed.

---

### 2) Download the project

Open a terminal and clone the repository:

```bash
git clone https://github.com/Jaden-Anthony/ETender-Evaluation-System.git
```

Then go into the folder:

```bash
cd ETender-Evaluation-System
```

---

### 3) Create a virtual environment

This keeps the project dependencies separate from the rest of your computer.

Using Python directly:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

You should now see `(.venv)` in your terminal prompt.

---

### 4) Install project dependencies

This project uses `uv` for dependency management.

If you do not have `uv` installed, install it:

```bash
pip install uv
```

Then install the project dependencies:

```bash
uv sync
```

If `uv sync` fails because the environment is not activated, make sure your virtual environment is active first.

---

### 5) Create your environment file

The project uses a `.env` file for configuration.

Create a file named `.env` in the project root and add:

```env
GMAIL_SENDER="your-email@gmail.com"
GMAIL_APP_PASSWORD="your-app-password"
TEAM_EMAILS="team@example.com,another@example.com"
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen2.5:14b"
MIN_RELEVANCE_SCORE="6.0"
MAX_TENDERS_TO_ANALYZE="60"
SEND_ZERO_MATCH_HEARTBEAT="true"
ENABLE_WINDOWS_TOAST="true"
```

Important notes:

- `GMAIL_SENDER` and `GMAIL_APP_PASSWORD` are only needed if you want email alerts.
- If you do not want to send emails, you can leave them blank.
- The project still works without email settings.
- `OLLAMA_MODEL` should match the model you downloaded earlier.

---

### 6) Run the project

To do a quick dry run (safe and lightweight test):

```bash
uv run python main.py --dry-run
```

This limits the scan and disables some actions so it is easier to test.

To run a normal scan:

```bash
uv run python main.py
```

To disable email and desktop notifications:

```bash
uv run python main.py --no-email --no-toast
```

To limit the number of tenders checked:

```bash
uv run python main.py --limit 20
```

---

### 7) Understand the output

When the project runs, it will:

- fetch tenders from the eTenders website
- filter likely matches
- use AI to score the opportunity
- export results to the `output/` folder
- save logs in the `logs/` folder

You will usually find output files like:

- `output/tenders_YYYYMMDD_HHMMSS.csv`
- `output/latest_matching_tenders.csv`

These files contain major details such as:

- tender number
- issuing authority
- province
- closing date
- keyword matches
- AI relevance score
- summary of the opportunity

---

## Common beginner issues

### Problem: `python` is not recognized

Try:

```bash
py --version
```

or reinstall Python and make sure "Add Python to PATH" is checked.

### Problem: `uv` is not found

Install it with:

```bash
pip install uv
```

Then verify:

```bash
uv --version
```

### Problem: Ollama is not running

Check whether Ollama is installed and running. Then test:

```bash
ollama list
```

If the model is not available, pull it:

```bash
ollama pull qwen2.5:14b
```

### Problem: the project cannot connect to the tender API

This usually happens when:

- your internet connection is down
- the eTenders website has changed its API format
- the script is being blocked by a request policy

Check the logs in the `logs/` folder and verify the URL in `src/config.py`.

### Problem: Gmail emails do not send

This usually means one of these:

- your Gmail app password is wrong
- your `TEAM_EMAILS` list is empty
- the account requires extra security setup

If you do not need emails, just leave those fields blank and run without email notifications.

---

## Running tests

The repository includes Python unit tests.

Run them with:

```bash
uv run pytest
```

---

## Example use case

Imagine you want to find tenders related to:

- AI-powered customer service chatbots
- digital marketing campaigns
- website portals and online services
- content creation and media work

Instead of manually checking the portal every day, this project scans the portal for you and surfaces only the most relevant opportunities.

---

## Project status

This is a functional project focused on real-world procurement intelligence and automation. It demonstrates how Python, APIs, AI, and workflow automation can be combined into a practical tool.

---

## Important note

This project is meant for opportunity discovery and internal strategic research. It does not replace formal procurement review, legal advice, compliance review, or bid submission support.

---


## License

This project does not currently declare a license. If you plan to share it publicly and want to make it open source, it is recommended to add a license such as MIT.

---

## Contributing

If you want to improve the project:

1. fork the repository
2. make your changes in a branch
3. run the tests
4. create a pull request with a clear explanation
