# GaddisAI System Architecture

## Overview

GaddisAI simulates National Security Council deliberations using multiple AI agents, each representing a government principal with distinct personas, priorities, and relationships with the President.

## Communication Model: Hub-and-Spoke

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUERY                               │
│              "Should we deploy troops?"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   RAG CONTEXT RETRIEVAL                      │
│  • Policy Memos (regional_strategy.txt)                     │
│  • Doctrine Documents (national_defense_strategy.txt)       │
│  • Agent Dossiers (SecDef.yaml, SecState.yaml, etc.)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              PARALLEL ADVISOR CONSULTATION                   │
│                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐│
│   │   SecDef     │    │  SecState    │    │     NSA      ││
│   │ Lloyd Austin │    │Antony Blinken│    │Jake Sullivan ││
│   └──────────────┘    └──────────────┘    └──────────────┘│
│          ↓                   ↓                   ↓          │
│   Recommendation      Recommendation      Recommendation    │
│   • deterrence: 0.8   • alliances: 0.8   • process: 0.8   │
│   • readiness: 0.7    • escalation: 0.7  • consensus: 0.7 │
│                                                              │
│   ◄──── Advisors can see each other's recommendations ────► │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  PRESIDENTIAL DECISION                       │
│                                                              │
│                    Joe Biden (President)                     │
│                                                              │
│   Weights each advisor's recommendation:                    │
│                                                              │
│   SecDef:                                                    │
│   • Relationship Score: 0.60 (personal trust)               │
│   • Interest Alignment: 0.78 (shared priorities)            │
│   • Final Weight: 0.67 = (0.6 × 0.60) + (0.4 × 0.78)       │
│                                                              │
│   SecState:                                                  │
│   • Relationship Score: 0.50                                │
│   • Interest Alignment: 0.82                                │
│   • Final Weight: 0.63                                      │
│                                                              │
│   NSA:                                                       │
│   • Relationship Score: 0.70                                │
│   • Interest Alignment: 0.71                                │
│   • Final Weight: 0.70                                      │
│                                                              │
│   → Makes final decision based on weighted advice           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT + AUDIT TRAIL                      │
│                                                              │
│  • All advisor recommendations (full text)                  │
│  • Advisor weights (relationship + alignment breakdown)     │
│  • Presidential decision (with rationale)                   │
│  • Saved to: output/deliberation_TIMESTAMP.json            │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. No Coordinator/Synthesizer

**Traditional NSC simulation might use:**
```
Advisors → NSA Coordinator → Synthesized Memo → President
```

**GaddisAI uses hub-and-spoke:**
```
Advisors → President (direct consultation)
```

Each advisor speaks directly to the President. No intermediary synthesis or filtering.

### 2. Relationship-Weighted Influence

The President doesn't treat all advisors equally. Influence is based on:

**Formula:**
```
Final Weight = (0.6 × Relationship Score) + (0.4 × Interest Alignment)
```

**Relationship Score (0.0 - 1.0):**
- Personal trust/favor the President has for this advisor
- Set manually in `config/roles.yaml`
- Examples:
  - 0.8 = High trust (close advisor, long relationship)
  - 0.5 = Neutral (professional respect but not close)
  - 0.3 = Low trust (political necessity, minimal influence)

**Interest Alignment (0.0 - 1.0):**
- How well advisor's recommendation aligns with President's priorities
- Calculated automatically by comparing priority weights
- Algorithm: Dot product of weight vectors, normalized
- Example:
  - President: `{deterrence: 0.8, alliances: 0.5}`
  - Advisor recommends strong deterrence measures
  - High alignment because recommendation matches President's high deterrence priority

### 3. Transparent Decision-Making

Every calculation is visible:

```
SecDef (Lloyd Austin):
├─ Relationship Score: 0.60  (from config)
├─ Interest Alignment: 0.78  (calculated from weights)
└─ Final Weight: 0.67        (0.6 × 0.60 + 0.4 × 0.78)
     └─ Explanation: SecDef's recommendation for military
        readiness aligns strongly with President's
        deterrence priorities (0.8), giving high alignment
        despite moderate personal relationship.
```

This allows you to:
- See why certain advisors had more influence
- Understand how relationship vs. alignment affected the outcome
- Audit decisions for bias or unexpected weighting

## Component Architecture

### Data Layer

```
data/
├── dossiers/          # Agent personas
│   ├── President.yaml
│   ├── SecDef.yaml
│   ├── SecState.yaml
│   └── NSA.yaml
├── memo/              # Policy memos (RAG source)
│   └── regional_strategy.txt
├── doctrine/          # Doctrine documents (RAG source)
│   └── national_defense_strategy.txt
└── chroma/            # Vector database (auto-generated)
```

### Configuration Layer

```
config/
├── roles.yaml         # Priority weights, red lines, relationships
└── retrieval.yaml     # RAG settings (embedding model, top-k)
```

### Application Layer

```
src/
├── rag/
│   ├── vectorstore.py      # ChromaDB interface
│   ├── ingest.py           # Document chunking & ingestion
│   └── retriever.py        # Context retrieval
├── agents/
│   ├── base_agent.py       # Base class (dossier loading, prompts)
│   ├── advisor_agent.py    # Advisor implementation
│   └── president_agent.py  # President with weighting logic
├── orchestrator.py         # LangGraph workflow
└── main.py                 # Entry point
```

## Workflow Details

### 1. Initialization Phase

```python
# Initialize RAG system
vectorstore = VectorStore(config)
ingester = DocumentIngester(config)
ingester.ingest_all()  # Chunk and embed documents
retriever = ContextRetriever(vectorstore)

# Initialize agents from dossiers
for dossier_file in data/dossiers/*.yaml:
    agent = AdvisorAgent(
        dossier=load_yaml(dossier_file),
        role_config=load_yaml(config/roles.yaml)[role]
    )

president = PresidentAgent(
    dossier=load_yaml("President.yaml"),
    relationships=config["President"]["advisor_relationships"]
)
```

### 2. Query Processing Phase

```python
# Step 1: Retrieve context
context = retriever.retrieve_for_query(
    query="Should we deploy troops?",
    include_types=["memo", "doctrine", "dossiers"]
)

# Step 2: Advisors consult (parallel)
recommendations = []
for advisor in [SecDef, SecState, NSA]:
    rec = advisor.generate_recommendation(
        query=query,
        context=context,
        other_recommendations=recommendations  # See others' positions
    )
    recommendations.append(rec)

# Step 3: President decides
decision = president.make_decision(
    query=query,
    context=context,
    advisor_recommendations=recommendations
)
```

### 3. Decision Weighting Algorithm

```python
def calculate_advisor_weight(advisor, recommendation):
    # 1. Get relationship score (from config)
    relationship_score = president.advisor_relationships[advisor.role]

    # 2. Calculate interest alignment
    alignment_score = calculate_alignment(
        president.weights,  # e.g., {deterrence: 0.8, alliances: 0.5}
        advisor.weights     # e.g., {deterrence: 0.9, readiness: 0.7}
    )

    # 3. Combine (60% relationship, 40% alignment)
    final_weight = (0.6 * relationship_score) + (0.4 * alignment_score)

    return final_weight

def calculate_alignment(president_weights, advisor_weights):
    # Dot product of common priority weights
    common_priorities = set(president_weights) & set(advisor_weights)

    dot_product = sum(
        president_weights[p] * advisor_weights[p]
        for p in common_priorities
    )

    max_possible = sum(
        max(president_weights[p], advisor_weights[p])
        for p in common_priorities
    )

    return dot_product / max_possible  # Normalized to 0-1
```

## Agent Behavior

### Advisor Agent

Each advisor has:

**Identity:**
- Person name (e.g., "Lloyd Austin")
- Official role (e.g., "Secretary of Defense")
- Mandate (responsibilities)

**Priorities:**
- Priority weights (e.g., `{deterrence: 0.8, readiness: 0.7}`)
- Higher weight = more important to this advisor

**Constraints:**
- Red lines (non-negotiable constraints)
- Example: "Maintain critical readiness thresholds"

**Knowledge:**
- Retrieved context from RAG (memos, doctrine)
- Other advisors' recommendations
- Recent actions and positions

**Output:**
```yaml
recommendation: "I recommend deploying 2,000 additional troops..."
rationale: "Based on my mandate to maintain readiness..."
risks: "Potential escalation with China..."
alternatives: "Alternative: Enhanced air presence without ground troops"
```

### President Agent

The President has:

**Identity:**
- Person name (e.g., "Joe Biden")
- Presidential priorities

**Relationships:**
- Favor/trust scores for each advisor
- Set in config, can be calibrated by research bots

**Priority Weights:**
- Personal priorities (e.g., `{alliances: 0.8, deterrence: 0.6}`)
- Used to calculate interest alignment

**Decision Process:**
1. Read all advisor recommendations
2. Calculate weight for each advisor (relationship + alignment)
3. Synthesize weighted advice
4. Apply own judgment and priorities
5. Make final decision

**Output:**
```yaml
decision: "I have decided to deploy 1,500 troops..."
rationale: "SecDef's recommendation carries significant weight (0.67)
           due to high alignment with my deterrence priorities.
           SecState raised valid concerns about allied cohesion..."
advisor_weights:
  SecDef: {relationship: 0.60, alignment: 0.78, final: 0.67}
  SecState: {relationship: 0.50, alignment: 0.82, final: 0.63}
  NSA: {relationship: 0.70, alignment: 0.71, final: 0.70}
```

## State Management (LangGraph)

```python
class DeliberationState(TypedDict):
    query: str                          # Original question
    context: str                        # Retrieved RAG context
    advisor_recommendations: List[Dict] # All advisor positions
    presidential_decision: Dict         # Final decision
    audit_trail: List[Dict]            # Full history
```

**Graph structure:**
```
Entry → retrieve_context → advisors_consult → president_decides → END
```

Linear flow because hub-and-spoke doesn't need complex routing.

## Extensibility

### Adding New Advisors

1. Create dossier YAML with persona
2. Add role config with weights and red lines
3. Add relationship score to President config
4. System auto-discovers and initializes

No code changes needed.

### Changing Decision Formula

Currently: `Final Weight = 0.6 × Relationship + 0.4 × Alignment`

To adjust, edit `president_agent.py`:

```python
def calculate_advisor_weight(self, advisor_role, recommendation):
    relationship_score = self.advisor_relationships[advisor_role]
    alignment_score = self.calculate_interest_alignment(recommendation)

    # Change these coefficients:
    final_weight = (0.7 * relationship_score) + (0.3 * alignment_score)
    # Or use different formula:
    # final_weight = relationship_score * alignment_score  # Multiplicative

    return final_weight
```

### Adding New Data Sources

Currently supports:
- Memos (policy documents)
- Doctrine (strategy documents)
- Dossiers (agent personas)

To add news or intelligence:

1. Add collection to `vectorstore.py`
2. Add ingestion method to `ingest.py`
3. Add retrieval logic to `retriever.py`
4. Configure in `config/retrieval.yaml`

## Performance Characteristics

**Initialization:**
- First run: ~30-60 seconds (document ingestion)
- Subsequent runs: ~5-10 seconds (vector DB already populated)

**Single Deliberation:**
- 3 advisors: ~20-40 seconds (3 parallel LLM calls + 1 President call)
- 5 advisors: ~30-50 seconds (scales with advisor count)

**Cost (OpenAI GPT-4):**
- Single deliberation: ~$0.10-0.30 (depends on context size)
- Per advisor: ~$0.03-0.08
- President decision: ~$0.05-0.10

**Optimization opportunities:**
- Use GPT-4-turbo instead of GPT-4 (faster, cheaper)
- Cache embeddings (already implemented)
- Batch similar queries

## Security & Privacy

**API Keys:**
- OpenAI API key required (set via environment variable)
- Never committed to code

**Data Storage:**
- All data stored locally
- Vector database: `data/chroma/`
- Deliberations: `output/*.json`
- No external logging or telemetry

**Prompt Safety:**
- Agent prompts constrained by red lines
- No arbitrary code execution
- RAG context filtered by relevance

## Future Enhancements

**Planned:**
1. Dynamic relationship scores (change based on advice quality)
2. News source integration (real-time context)
3. Multi-turn deliberations (advisors can respond to President's questions)
4. Scenario branching (explore "what if" alternatives)
5. Visual output (decision tree diagrams)

**Under consideration:**
1. Voice mode (audio input/output)
2. Web interface (instead of CLI)
3. Multi-president simulations (compare different administrations)
4. Historical validation (test against known decisions)
