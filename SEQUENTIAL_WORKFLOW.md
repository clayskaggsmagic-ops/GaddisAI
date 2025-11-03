# Sequential Meeting Workflow Guide

## Overview

The sequential meeting workflow implements a one-on-one meeting pattern between the President and each advisor. This is different from the original hub-and-spoke workflow where all advisors provide recommendations simultaneously.

### Workflow Pattern

1. **Random Meeting Order**: Advisors meet with President in random order
2. **Problem Presentation**: Each advisor presents 3 pressing policy problems
3. **Presidential Selection**: President selects 1 problem and asks a follow-up question
4. **Advisor Response**: Advisor answers the question in detail
5. **Full Awareness**: Each subsequent advisor is aware of previous meetings
6. **Policy Synthesis**: President synthesizes all discussions into NSC policy document

## Installation

### 1. Set up virtual environment (if not already done):
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Sequential Workflow (New)

**Autonomous mode (RECOMMENDED - No query needed!):**
```bash
python src/main.py --sequential
```
The system automatically:
- Reads Foreign Affairs articles from `data/memo/` directory
- Each advisor identifies 3 policy problems from their domain perspective
- President engages with each advisor (selects problem, asks question, gets answer)
- Generates comprehensive NSC policy document

**With custom query (optional):**
```bash
python src/main.py --sequential --query "What should our approach to China be?"
```

### Hub-and-Spoke Workflow (Original)

**Single query mode:**
```bash
python src/main.py --query "What should our approach to China be?"
```

**Interactive mode:**
```bash
python src/main.py
```

## Command-Line Options

- `--sequential`: Use sequential meeting workflow instead of hub-and-spoke
- `--query "..."`: Run single query and exit (otherwise enters interactive mode)
- `--model gpt-4-turbo`: Specify OpenAI model (default: gpt-4-turbo)
- `--reingest`: Force re-ingestion of all documents
- `--no-memory`: Disable memory system
- `--config-dir ./config`: Path to config directory
- `--data-dir ./data`: Path to data directory

## Expected Output

### Sequential Workflow Output

```
=== NSC Sequential Meetings ===
Scenario: What should our approach to China be?

Meeting order: SecDef, VP, SecState

  Meeting 1/3: Pete Hegseth (SecDef)
    Pete Hegseth presenting problems...
    President selecting problem...
    Pete Hegseth answering question...

  Meeting 2/3: JD Vance (VP)
    JD Vance presenting problems...
    President selecting problem...
    JD Vance answering question...

  Meeting 3/3: Marco Rubio (SecState)
    Marco Rubio presenting problems...
    President selecting problem...
    Marco Rubio answering question...

  President synthesizing policy document...

Sequential meetings complete.

[Formatted output with all meetings and final NSC policy document]
```

## Cost Estimates

With `gpt-4-turbo` (default model):

- **Hub-and-Spoke**: ~$0.20-$0.25 per deliberation (4 LLM calls)
- **Sequential**: ~$0.60-$0.80 per deliberation (10 LLM calls)

Sequential workflow costs more because it involves:
- 3 advisors × 3 calls each = 9 calls (problems, selection, answer)
- 1 final synthesis call
- Total: 10 LLM calls vs 4 in hub-and-spoke

## Architecture

### New Agent Methods

**AdvisorAgent:**
- `present_problems()`: Present 3 policy problems based on context
- `answer_question()`: Answer President's follow-up question

**PresidentAgent:**
- `select_problem_and_question()`: Select 1 of 3 problems and formulate question
- `synthesize_policy_document()`: Create comprehensive NSC policy document

### Orchestration

**SequentialMeetingState**: Tracks meeting progress
- `advisor_order`: Randomized list of advisors
- `current_meeting_index`: Current meeting number
- `completed_meetings`: List of all meeting transcripts
- `policy_document`: Final synthesized document

**Workflow Nodes:**
- `_conduct_meeting_node()`: Run one advisor-president meeting
- `_should_continue_meetings()`: Conditional routing (continue or synthesize)
- `_president_synthesizes_node()`: Create final policy document

## Memory System Integration

The sequential workflow fully integrates with the memory system:

- **After each meeting**: Stores observations for both advisor and President
- **Problem presentation**: Advisors see previous meeting summaries
- **President's decisions**: Informed by memories of past deliberations
- **Policy synthesis**: Draws on all stored memories

## Testing

Run the test script to verify implementation:

```bash
python test_sequential.py
```

This tests:
- Module imports
- Method existence
- Method signatures
- State definition

## Troubleshooting

### "No module named 'yaml'" or similar
Make sure you're using the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "OPENAI_API_KEY environment variable not set"
Set your API key:
```bash
export OPENAI_API_KEY='your-key-here'
```

### ChromaDB initialization slow
First run takes longer as it initializes the vector database. Subsequent runs are faster.

### High costs
- Use `--model gpt-4o-mini` for cheaper runs (~$0.08-$0.10 per deliberation)
- Disable memory with `--no-memory` to save ~10% on tokens
- Sequential workflow costs 3-4× more than hub-and-spoke due to more LLM calls

## Implementation Details

### Files Modified

1. **src/agents/advisor_agent.py**
   - Added `present_problems()` method
   - Added `answer_question()` method
   - Added `_parse_problems()` helper

2. **src/agents/president_agent.py**
   - Added `select_problem_and_question()` method
   - Added `synthesize_policy_document()` method
   - Added `_parse_problem_selection()` helper

3. **src/orchestrator.py**
   - Added `SequentialMeetingState` TypedDict
   - Added `_conduct_meeting_node()` method
   - Added `_should_continue_meetings()` conditional
   - Added `_president_synthesizes_node()` method
   - Added `_build_sequential_graph()` method
   - Added `deliberate_sequential()` entry point
   - Added `format_sequential_output()` formatter

4. **src/main.py**
   - Added `--sequential` CLI flag
   - Updated `interactive_mode()` to support sequential
   - Updated `single_query_mode()` to support sequential
   - Routes to appropriate workflow based on flag

### Design Principles

- **Simple and modular**: Each method has one clear purpose
- **No duplication**: Reuses existing RAG and memory systems
- **Clean separation**: Sequential workflow independent of hub-and-spoke
- **Token tracking**: Full cost transparency across both workflows
- **Memory integration**: Seamless integration with existing memory system

## Next Steps

1. Set your API key
2. Run the test script to verify installation
3. Try a simple query with `--sequential`
4. Compare outputs between sequential and hub-and-spoke workflows
5. Adjust model and parameters based on your cost/quality preferences
