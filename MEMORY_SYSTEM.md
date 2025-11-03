# Memory System for GaddisAI

## Overview

The memory system implements a **Generative Agents-style memory architecture** that allows Trump and advisors to remember past deliberations, decisions, and interactions. This is based on the paper *"Generative Agents: Interactive Simulacra of Human Behavior"* (Park et al., 2023).

## Key Features

### 1. **Memory Stream**
- Each agent maintains a chronological stream of observations
- Memories are stored with timestamps, importance scores, and embeddings
- Types of memories:
  - **Observations**: Direct experiences (e.g., "I recommended military intervention...")
  - **Reflections**: Synthesized insights (e.g., "Bolton tends to favor military solutions...")

### 2. **Smart Retrieval**
When agents need to make decisions, the system retrieves relevant memories using a weighted scoring formula:

```
Memory Score = 0.4 × Relevance + 0.3 × Recency + 0.3 × Importance
```

- **Relevance**: Vector similarity to current query
- **Recency**: Exponential decay (half-life: 7 days)
- **Importance**: 0-1 score (presidential decisions = 0.9, reflections = 0.95)

### 3. **Automatic Reflection**
- After every 10 observations, agents automatically generate reflections
- Reflections synthesize patterns from recent memories
- Example: "I've noticed that Mattis' cautious approach has proven accurate in 7 of 10 cases"

### 4. **Memory Injection into Prompts**
Retrieved memories are injected into agent prompts:

```
## Your Relevant Memories from Past Deliberations

- [November 2, 2025 at 02:30 PM] I recommended diplomatic engagement on North Korea issue
- [November 1, 2025 at 10:15 AM] I decided to pursue military deterrence after Mattis convinced me

**[REFLECTION]** (November 3, 2025)
  Bolton's recommendations have led to unintended escalation in 3 of 5 cases
```

## Architecture

### Workflow Integration

```
1. retrieve_context → Retrieves RAG context + Agent memories
2. advisors_consult → Advisors see their memories when recommending
3. president_decides → President sees his memories when deciding
4. reflect_and_store → Stores observations, generates reflections
5. END
```

### Storage

- **Backend**: ChromaDB (same database as RAG system)
- **Collection**: `agent_memories`
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Persistence**: Automatic via ChromaDB

## Configuration

See `config/memory.yaml`:

```yaml
retrieval:
  top_k: 5  # Retrieve 5 memories per agent
  relevance_weight: 0.4
  recency_weight: 0.3
  importance_weight: 0.3

reflection:
  observation_threshold: 10  # Reflect every 10 observations
  enabled: true

decay:
  half_life_days: 7  # Memories decay 50% every 7 days
```

## Usage

### Enable Memory (Default)
```bash
python src/main.py
```

### Disable Memory
```bash
python src/main.py --no-memory
```

### View Memory Statistics
```python
from memory.memory_store import MemoryStore

memory_store = MemoryStore(
    config_path="./config/memory.yaml",
    persist_directory="./data/chroma"
)

print(f"Total memories: {memory_store.get_memory_count()}")
print(f"President memories: {memory_store.get_memory_count('President')}")
print(f"SecDef memories: {memory_store.get_memory_count('SecDef')}")
```

### Clear Memories
```python
# Clear all memories
memory_store.clear_memories()

# Clear specific agent's memories
memory_store.clear_memories(agent_role="President")
```

## Example: Memory in Action

### First Deliberation
**Query**: "Should we deploy troops to the Indo-Pacific?"

**President's Decision**: "Deploy carrier strike group, per Mattis' recommendation"

**Stored Observation**:
- "I decided to deploy carrier strike group on question 'Should we deploy troops to Indo-Pacific?'. I gave most weight to SecDef."
- Importance: 0.9
- Timestamp: 2025-11-03T14:30:00

### Second Deliberation (3 days later)
**Query**: "China is increasing naval activity near Taiwan. What should we do?"

**Retrieved Memory**:
- [November 3, 2025 at 02:30 PM] I decided to deploy carrier strike group on question 'Should we deploy troops to Indo-Pacific?'. I gave most weight to SecDef.
- Final Score: 0.85 (high relevance, recent, high importance)

**President's Decision**: "I recall my recent deployment decision. Consistent with that, I will..."

## Key Differences from Original Paper

| Feature | Generative Agents Paper | GaddisAI Implementation |
|---------|------------------------|------------------------|
| **Environment** | Spatial grid world | Policy deliberation (no spatial model) |
| **Interactions** | Continuous, multi-turn | Single-turn deliberations |
| **Planning** | Multi-level (daily/hourly) | Decision-based only |
| **Reflection Trigger** | Accumulated importance > 150 | Every 10 observations |
| **Memory Types** | Observations, reflections, plans | Observations, reflections |

## Benefits

### For Realistic Simulation
- Trump remembers past decisions and their outcomes
- Advisors can reference their track record
- Relationships evolve based on performance
- Consistency across deliberations

### For Research
- Analyze how memory affects decision-making
- Track advisor influence over time
- Study learning and adaptation patterns
- Compare memory-enabled vs memory-disabled simulations

## Implementation Files

- `src/memory/memory_store.py` - Core memory storage and retrieval (350 lines)
- `config/memory.yaml` - Memory system configuration
- `src/orchestrator.py` - Workflow integration (memory retrieval & storage nodes)
- `src/agents/base_agent.py` - Memory injection into prompts
- `src/agents/advisor_agent.py` - Advisor memory handling
- `src/agents/president_agent.py` - Presidential memory handling

## Future Enhancements

### Phase 2 (Not Implemented)
- [ ] Dynamic relationship scoring based on advisor accuracy
- [ ] Multi-turn deliberations with memory of conversation
- [ ] Importance scoring based on actual outcomes (feedback loop)
- [ ] Memory consolidation (merge similar memories)
- [ ] Forgetting mechanism (remove low-importance old memories)

## References

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *UIST 2023*.

https://arxiv.org/abs/2304.03442
