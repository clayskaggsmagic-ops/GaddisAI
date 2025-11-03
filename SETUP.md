# GaddisAI Setup Guide

## Quick Start

### 1. Create Virtual Environment

Your system requires a Python virtual environment. Create one:

```bash
cd "/Users/clayskaggs/Library/Mobile Documents/com~apple~CloudDocs/projects/GaddisAI"
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

### 3. Set OpenAI API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or add to your shell profile (~/.zshrc or ~/.bash_profile):

```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Verify Setup

Run the test script:

```bash
python test_system.py
```

You should see:
```
✓ All tests passed! System is ready.
```

### 5. Run First Deliberation

```bash
python src/main.py
```

Then enter a policy question like:
```
Policy Question: Should we deploy additional troops to the Indo-Pacific?
```

## Installation Troubleshooting

### "externally-managed-environment" Error

This means your system Python is managed by Homebrew. You MUST use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Virtual Environment Not Activating

Make sure you're in the project directory and the venv was created:

```bash
cd "/Users/clayskaggs/Library/Mobile Documents/com~apple~CloudDocs/projects/GaddisAI"
ls -la venv  # Should show the virtual environment directory
source venv/bin/activate  # You should see (venv) in your prompt
```

### Missing Dependencies

If imports fail, reinstall in the virtual environment:

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### OpenAI API Key Issues

Verify your key is set:

```bash
echo $OPENAI_API_KEY
```

Should print your key (starting with "sk-"). If empty, export it:

```bash
export OPENAI_API_KEY='sk-your-key-here'
```

## Running the System

### Always Activate Virtual Environment First

Before running any commands:

```bash
cd "/Users/clayskaggs/Library/Mobile Documents/com~apple~CloudDocs/projects/GaddisAI"
source venv/bin/activate
```

You should see `(venv)` in your command prompt.

### Interactive Mode

```bash
python src/main.py
```

Ask multiple questions in one session.

### Single Query Mode

```bash
python src/main.py --query "Your policy question here"
```

### Re-ingest Documents

If you add new documents or modify existing ones:

```bash
python src/main.py --reingest
```

### Use Different Model

```bash
python src/main.py --model gpt-4-turbo
```

Available models:
- `gpt-4` (default, most capable)
- `gpt-4-turbo` (faster, cheaper)
- `gpt-3.5-turbo` (fastest, cheapest, less capable)

## Next Steps After Setup

### 1. Customize Relationships

Edit [config/roles.yaml](config/roles.yaml):

```yaml
President:
  advisor_relationships:
    NSA: 0.7      # Adjust these scores (0.0 to 1.0)
    SecDef: 0.6   # Higher = more influence on President
    SecState: 0.5
```

### 2. Generate Better Dossiers

The current dossiers are templates. Generate better ones with research:

```bash
python src/generate_dossiers.py --role SecDef --person "Pete Hegseth"
```

### 3. Add More Documents

Add policy memos and doctrine to:
- `data/memo/*.txt`
- `data/doctrine/*.txt`

Then re-ingest:

```bash
python src/main.py --reingest
```

### 4. Test with Real Questions

Try questions like:
- "Should we deploy additional troops to the Indo-Pacific?"
- "How should we respond to Iran's nuclear program?"
- "What's our strategy for deterring China in the South China Sea?"

## Common Workflows

### Adding a New Advisor

1. Create dossier:
```bash
python src/generate_dossiers.py --role CJCS --person "Charles Q. Brown Jr."
```

2. Add role config in `config/roles.yaml`:
```yaml
CJCS:
  weights:
    deterrence: 0.85
    readiness: 0.9
    alliances: 0.6
  red_lines:
    - "Maintain force readiness above threshold"
```

3. Add relationship to President:
```yaml
President:
  advisor_relationships:
    CJCS: 0.75
```

4. Re-ingest and run:
```bash
python src/main.py --reingest
```

### Calibrating for a Different President

1. Generate President dossier:
```bash
python src/generate_dossiers.py --role President --person "Donald Trump"
```

2. Adjust priority weights in `config/roles.yaml`:
```yaml
President:
  weights:
    deterrence: 0.8     # Trump prioritizes strength
    escalation: 0.7
    alliances: 0.3      # Less emphasis on traditional alliances
    budget: 0.5
```

3. Calibrate advisor relationships:
```yaml
President:
  advisor_relationships:
    NSA: 0.6
    SecDef: 0.8    # Strong relationship with military
    SecState: 0.4   # Lower trust in diplomacy
```

4. Re-ingest and test:
```bash
python src/main.py --reingest --query "Should we withdraw from NATO?"
```

## File Organization

```
Your working directory:
/Users/clayskaggs/Library/Mobile Documents/com~apple~CloudDocs/projects/GaddisAI

Important files:
├── venv/                    # Virtual environment (you create this)
├── src/main.py             # Run this to start deliberations
├── config/roles.yaml       # Edit advisor relationships here
├── data/dossiers/          # Agent personas
└── output/                 # Saved deliberations appear here
```

## Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

This removes `(venv)` from your prompt and returns to system Python.

## Getting Help

If you encounter issues:

1. Check you're in the virtual environment: `(venv)` in prompt
2. Check API key is set: `echo $OPENAI_API_KEY`
3. Re-run tests: `python test_system.py`
4. Check Python version: `python --version` (should be 3.8+)

## System Architecture Reminder

```
User Query
    ↓
RAG Retrieval (context from memos, doctrine)
    ↓
Advisors Generate Recommendations (parallel)
  - SecDef
  - SecState
  - NSA
  (All see each other's recommendations)
    ↓
President Weighs Advice
  - Relationship score (favor/trust)
  - Interest alignment (shared priorities)
  - Final decision
    ↓
Output + Audit Trail
```

Key features:
- **Hub-and-spoke**: Advisors → President (no coordinator)
- **Relationship weighting**: President favors certain advisors
- **Interest alignment**: Recommendations aligned with President's priorities have more weight
- **Full transparency**: All reasoning and weights are logged
