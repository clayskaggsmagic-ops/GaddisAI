# GaddisAI Quick Start Guide

Get up and running with GaddisAI NSC simulator in minutes.

## First-Time Setup (5 minutes)

### 1. Prerequisites
- Python 3.11 or 3.12 (Python 3.13+ not yet supported due to ChromaDB compatibility)
- OpenAI API key

### 2. Installation

```bash
# Navigate to project
cd GaddisAI

# Create virtual environment with Python 3.12
python3.12 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key (replace with your key)
export OPENAI_API_KEY='sk-your-key-here'

# Optional: Test installation
python test_system.py
```

## Running the System

GaddisAI supports two workflows:

### Option 1: Autonomous Sequential Mode (Recommended for First Run)

**Fully autonomous** - agents analyze Foreign Affairs articles and generate policy recommendations without any user input.

```bash
# Activate virtual environment
source venv/bin/activate

# Run autonomous mode
python src/main.py --sequential
```

**That's it!** The system will:
1. Load the Foreign Affairs article on US-China New Cold War
2. Randomize advisor meeting order
3. Each advisor presents 3 problems from their perspective
4. President meets with each advisor one-on-one
5. Generate comprehensive NSC policy document

#### What the Agents Analyze
- **Foreign Affairs Article**: "The Divided World: The New Cold War" by Hal Brands & John Lewis Gaddis
- **Topics**: US-China strategic competition, alliance management, military readiness, diplomatic priorities

#### Expected Output
```
============================================================
AUTONOMOUS MODE: Agents will analyze Foreign Affairs articles
and generate national security policy recommendations
============================================================

=== Initializing RAG System ===
Vector store already populated

=== Initializing NSC Orchestrator ===
Initialized President: Donald J. Trump
Initialized SecDef: Pete Hegseth
Initialized SecState: Marco Rubio
Initialized VP: JD Vance

=== NSC Sequential Meetings ===
Meeting order: VP, SecDef, SecState

  Meeting 1/3: JD Vance (VP)
    JD Vance presenting problems...
    President selecting problem...
    JD Vance answering question...

[Full output with meeting transcripts and NSC policy document]
```

#### Sequential Mode Options
```bash
# Basic autonomous mode
python src/main.py --sequential

# With cheaper model (reduce costs ~80%)
python src/main.py --sequential --model gpt-4o-mini

# Disable memory system (saves ~10% tokens)
python src/main.py --sequential --no-memory

# With custom scenario instead of autonomous
python src/main.py --sequential --query "Your custom scenario here"
```

#### Cost Estimate
- **gpt-4-turbo** (default): ~$0.60-$0.80 per run
- **gpt-4o-mini**: ~$0.10-$0.15 per run

### Option 2: Interactive Hub-and-Spoke Mode

Ask policy questions interactively and get multi-advisor deliberations.

```bash
# Activate virtual environment
source venv/bin/activate

# Run interactive mode
python src/main.py

# Ask your question at the prompt
Policy Question: Should we deploy additional troops to the Indo-Pacific?
```

#### How Hub-and-Spoke Works
```
       SecDef ──┐
                │
     SecState ──┼──> PRESIDENT ──> Decision
                │
         VP   ──┘
```

- Each advisor talks directly to President
- Advisors can see each other's recommendations
- President weighs advice based on relationships and alignment
- President makes final call

#### Understanding the Output

**1. Advisor Recommendations** - Each advisor gives their position:
```
### Pete Hegseth (SecDef)

Priority Weights: {'deterrence': 0.8, 'readiness': 0.7, ...}
Red Lines: ['Maintain critical readiness thresholds']

Recommendation: [Full detailed recommendation]
```

**2. Presidential Decision** - President weighs all advice:
```
### Donald J. Trump

Advisor Influence Weights:
  - SecDef:
    * Relationship Score: 0.60
    * Interest Alignment: 0.75
    * Final Weight: 0.66
  - SecState:
    * Relationship Score: 0.50
    * Interest Alignment: 0.82
    * Final Weight: 0.63

Decision: [Full decision with rationale]
```

#### Interactive Mode Options
```bash
# Basic interactive mode
python src/main.py

# Single query (non-interactive)
python src/main.py --query "Your policy question here"

# With different model
python src/main.py --model gpt-4-turbo
```

## Using the Helper Script

```bash
# Run with defaults
./run.sh

# With a single query
./run.sh --query "Should we respond militarily to cyberattacks?"

# With different model
./run.sh --model gpt-4-turbo
```

## Customization

### Change Advisor Relationships

Edit `config/roles.yaml`:

```yaml
President:
  advisor_relationships:
    SecDef: 0.8    # High trust (strong influence)
    SecState: 0.4  # Low trust (weak influence)
    VP: 0.7        # Moderate trust
```

### Change President's Priorities

```yaml
President:
  weights:
    deterrence: 0.9   # Very important
    alliances: 0.3    # Less important
    budget: 0.5       # Moderately important
```

These weights affect:
1. How President thinks about problems
2. Which advisors' recommendations align with President's interests

### Add More Advisors

```bash
# Generate new dossier
python src/generate_dossiers.py --role CJCS --person "Charles Q. Brown"

# Add to config/roles.yaml and re-ingest
python src/main.py --reingest
```

## Output Files

All deliberations are automatically saved to `output/` directory:

**Sequential mode:**
- `sequential_YYYYMMDD_HHMMSS/` folder containing:
  - `NSC_Policy_Memo.md` - Final policy document
  - `meeting_01_*.md` through `meeting_N_*.md` - Individual meeting transcripts
  - `index.md` - Index of all meetings
  - `raw_data.json` - Raw deliberation data

**Hub-and-spoke mode:**
- `deliberation_YYYYMMDD_HHMMSS_query.json` - JSON file with full deliberation

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
```bash
export OPENAI_API_KEY='your-key-here'
```

### "No module named X"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "command not found: python"
Use `python3` or ensure venv is activated

### Python 3.13 import hangs for 5+ minutes
ChromaDB doesn't support Python 3.13 yet. Use Python 3.11 or 3.12:
```bash
# Install Python 3.12
brew install python@3.12

# Recreate venv
rm -rf venv
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### First run takes a long time
- First run ingests all documents (~30 seconds)
- ChromaDB initialization can be slow (~30 seconds)
- Subsequent runs are much faster (10-20 seconds)

### No advisors showing up
Run with `--reingest` flag to reload documents

### Empty recommendations
Check that dossier files exist in `data/dossiers/`

## Pro Tips

1. **See the math**: The output shows exactly how relationship and alignment scores combine to create final weights

2. **Audit trail**: Every deliberation is saved with full details for later review

3. **Iterate quickly**: Change relationships in `config/roles.yaml` and immediately run another query to see how it affects decisions

4. **Test scenarios**: Ask the same question with different relationship scores to see how presidential favor affects outcomes

5. **Compare workflows**: Try both sequential and hub-and-spoke modes on the same scenario to see different dynamics

## When You're Done

```bash
deactivate  # Exit virtual environment
```

## Next Steps

1. **Try both workflows** - Sequential for autonomous analysis, hub-and-spoke for specific questions
2. **Read [ARCHITECTURE.md](ARCHITECTURE.md)** for system design details
3. **Read [SEQUENTIAL_WORKFLOW.md](SEQUENTIAL_WORKFLOW.md)** for sequential mode deep dive
4. **Experiment** with different relationship scores and questions
5. **Calibrate** for different administrations by adjusting weights and relationships

## Additional Documentation

- **[README.md](README.md)** - Full system overview and features
- **[SETUP.md](SETUP.md)** - Detailed installation and configuration guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[COST_GUIDE.md](COST_GUIDE.md)** - Cost tracking and optimization
- **[MEMORY_SYSTEM.md](MEMORY_SYSTEM.md)** - Agent memory system details
- **[SEQUENTIAL_WORKFLOW.md](SEQUENTIAL_WORKFLOW.md)** - Sequential meeting workflow
