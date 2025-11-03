# GaddisAI: NSC Policy Deliberation Simulator

A multi-agent AI system that simulates National Security Council deliberations. Each agent represents a government principal (SecDef, SecState, NSA, etc.) with their own persona, priorities, and constraints. The President weighs their advice based on personal relationships and interest alignment, then makes the final decision.

## Architecture

### Hub-and-Spoke Model

```
         Advisors (parallel)
              |
    SecDef    |    SecState    |    NSA
       \      |      /
        \     |     /
         PRESIDENT
              |
          Decision
```

- **No coordinator synthesis**: Each advisor meets directly with the President
- **Advisors see each other's recommendations**: Positions are shared across advisors
- **Relationship-weighted influence**: President has favor/trust scores for each advisor
- **Interest alignment scoring**: President compares recommendations against his own priorities
- **Full audit trail**: All reasoning, weights, and decisions are logged

## System Components

### 1. RAG System ([src/rag/](src/rag/))
- **VectorStore**: ChromaDB-based vector database for document storage
- **DocumentIngester**: Processes and chunks memos, doctrine, dossiers
- **ContextRetriever**: Retrieves relevant context for agent queries

### 2. Agents ([src/agents/](src/agents/))
- **NSCAgent**: Base class with dossier loading and prompt construction
- **AdvisorAgent**: Generates structured recommendations (SecDef, SecState, NSA)
- **PresidentAgent**: Weighs advice and makes final decisions

### 3. Orchestrator ([src/orchestrator.py](src/orchestrator.py))
- LangGraph-based workflow orchestration
- Hub-and-spoke deliberation pattern
- State management and audit trail

### 4. Configuration
- **[config/roles.yaml](config/roles.yaml)**: Priority weights, red lines, relationships
- **[config/retrieval.yaml](config/retrieval.yaml)**: RAG settings, top-k values
- **[data/dossiers/](data/dossiers/)**: Agent personas (President, SecDef, SecState, NSA)

## Requirements

- **Python 3.11 or 3.12** (Python 3.13+ not yet supported due to ChromaDB compatibility)
- OpenAI API key
- ~500MB disk space for dependencies

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

### 3. Verify Data Structure

Ensure you have:
- `data/dossiers/` - Agent persona YAML files
- `data/memo/` - Policy memos (`.txt` files)
- `data/doctrine/` - Doctrine documents (`.txt` files)
- `config/roles.yaml` - Role configurations
- `config/retrieval.yaml` - RAG settings

## Usage

### Interactive Mode

Ask multiple policy questions in a session:

```bash
python src/main.py
```

Example interaction:
```
Policy Question: Should we deploy additional troops to the Indo-Pacific?
[Full deliberation with advisor recommendations and presidential decision]

Policy Question: How should we respond to increased Russian activity in the Arctic?
[Another deliberation]
```

### Single Query Mode

Run a single deliberation and exit:

```bash
python src/main.py --query "Should we deploy additional troops to the Indo-Pacific?"
```

### Options

```bash
python src/main.py --help

Options:
  --query, -q          Single policy question (omit for interactive mode)
  --reingest          Force re-ingestion of all documents
  --model             OpenAI model to use (default: gpt-4)
  --config-dir        Path to config directory (default: ./config)
  --data-dir          Path to data directory (default: ./data)
```

### Examples

```bash
# Interactive mode with GPT-4
python src/main.py

# Single query with specific model
python src/main.py --query "How should we handle Iran's nuclear program?" --model gpt-4-turbo

# Re-ingest documents and run query
python src/main.py --reingest --query "What's our strategy for deterring China?"
```

## Output

### Console Output

Each deliberation shows:

1. **Advisor Recommendations**
   - Each advisor's full recommendation
   - Their priority weights
   - Their red lines (constraints)

2. **Presidential Decision**
   - Advisor influence weights breakdown:
     - Relationship score (how much President favors them)
     - Interest alignment score (how recommendations align with President's priorities)
     - Final weight (combined score)
   - President's decision with full rationale
   - Implementation guidance

### Saved Files

Deliberations are automatically saved to `output/` directory:

```
output/deliberation_20250103_143022_Should_we_deploy_additional_troops.json
```

Each file contains:
- Original query
- Retrieved context
- All advisor recommendations
- Presidential decision with weights
- Full audit trail

## How It Works

### 1. Context Retrieval

When you ask a question, the RAG system retrieves relevant:
- Policy memos (e.g., regional strategy documents)
- Doctrine (e.g., National Defense Strategy)
- Agent dossiers (for persona consistency)

### 2. Advisor Consultation

Each advisor (SecDef, SecState, NSA) generates a recommendation based on:
- Their dossier (role, mandate, priorities, positions)
- Their priority weights (how much they care about deterrence, alliances, budget, etc.)
- Their red lines (non-negotiable constraints)
- Retrieved context
- Other advisors' recommendations (they see each other's positions)

### 3. Presidential Decision

The President:
1. Reads all advisor recommendations
2. Calculates influence weight for each advisor:
   - **Relationship score** (0.0-1.0): How much President favors this advisor
   - **Interest alignment** (0.0-1.0): How well recommendation aligns with President's priorities
   - **Final weight** = 60% relationship + 40% alignment
3. Weighs all advice based on these scores
4. Makes final decision based on weighted input and own judgment

### 4. Audit Trail

Everything is logged for transparency:
- What context was retrieved
- What each advisor recommended and why
- How each advisor was weighted
- What the President decided and why

## Customization

### Adding New Advisors

1. Create dossier YAML in `data/dossiers/`:
```yaml
person: "Jane Smith"
role: "National Security Advisor"
mandate: "Coordinate national security policy..."
# ... rest of dossier
```

2. Add role config in `config/roles.yaml`:
```yaml
NSA:
  weights:
    process: 0.8
    consensus: 0.7
  red_lines:
    - "No decision without all principals consulted"
```

3. Add relationship in President's config:
```yaml
President:
  advisor_relationships:
    NSA: 0.7  # Favor/trust score
```

The system will automatically discover and initialize the new advisor.

### Adjusting Relationship Scores

Edit `config/roles.yaml`:

```yaml
President:
  advisor_relationships:
    SecDef: 0.8   # High favor - military focused President
    SecState: 0.4 # Lower favor - less trust in diplomacy
    NSA: 0.7      # Moderate favor
```

Higher scores = more influence on President's decisions.

### Changing Priority Weights

Edit weights for any role in `config/roles.yaml`:

```yaml
SecDef:
  weights:
    deterrence: 0.9   # Very focused on deterrence
    readiness: 0.8
    alliances: 0.3    # Less concerned with alliances
    budget: 0.2       # Budget is secondary
```

These affect both:
- How the advisor formulates recommendations
- How the President calculates interest alignment

## Generating Dossiers

Use the dossier generation tool to create/update agent personas:

```bash
# Generate all dossiers
python src/generate_dossiers.py

# Generate specific role
python src/generate_dossiers.py --role SecDef --person "Lloyd Austin"

# Options
python src/generate_dossiers.py --help
```

## Project Structure

```
GaddisAI/
├── src/
│   ├── agents/
│   │   ├── base_agent.py       # Base agent class
│   │   ├── advisor_agent.py    # Advisor implementation
│   │   └── president_agent.py  # President with weighting logic
│   ├── rag/
│   │   ├── vectorstore.py      # ChromaDB vector database
│   │   ├── ingest.py           # Document ingestion
│   │   └── retriever.py        # Context retrieval
│   ├── orchestrator.py         # LangGraph orchestration
│   ├── main.py                 # Application entry point
│   ├── researcher.py           # Dossier research (existing)
│   └── generate_dossiers.py    # Dossier generation CLI (existing)
├── config/
│   ├── roles.yaml              # Role configs, weights, relationships
│   └── retrieval.yaml          # RAG configuration
├── data/
│   ├── dossiers/               # Agent personas
│   ├── memo/                   # Policy memos
│   ├── doctrine/               # Doctrine documents
│   └── chroma/                 # Vector database (created on first run)
├── output/                     # Saved deliberations (created on first run)
├── requirements.txt
└── README.md
```

## Next Steps

1. **Test the system**: Run a sample deliberation to verify everything works
2. **Add more documents**: Expand `data/memo/` and `data/doctrine/` with relevant policy documents
3. **Calibrate relationships**: Adjust President's advisor relationships in `config/roles.yaml`
4. **Generate better dossiers**: Use `generate_dossiers.py` with real research to create accurate personas
5. **Add news ingestion**: Implement news source integration for real-time context

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
Set your API key:
```bash
export OPENAI_API_KEY='sk-...'
```

### Empty deliberations or missing advisors
Run with `--reingest` to rebuild vector database:
```bash
python src/main.py --reingest
```

### Import errors
Make sure you're in the project root and all dependencies are installed:
```bash
pip install -r requirements.txt
```

## License

[Your License Here]
