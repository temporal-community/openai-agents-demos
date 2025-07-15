# Enhanced Research Workflow with Clarifying Questions

This enhanced research workflow implements a multi-agent system that can ask clarifying questions before conducting deep research, based on the patterns from the [OpenAI Deep Research API cookbook](https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api_agents).

## Architecture

### Agent Flow

```
User Query → Triage Agent → Decision
                    ↓
            Clarification Needed?
                    ↓
        ┌─── Yes: Clarifying Agent → Questions → User Input
        │                    ↓
        │            Instruction Agent → Enriched Query
        │                    ↓
        └─── No: Instruction Agent → Direct Research
                            ↓
                    Planner Agent → Search Agent → Writer Agent
                            ↓
                    Research Result
```

### Key Components

1. **TriageAgent** (`triage_agent.py`)
   - Uses `gpt-4o-mini` for fast decisions
   - Routes to clarifying or instruction agent based on query completeness

2. **ClarifyingAgent** (`clarifying_agent.py`)
   - Generates 2-3 smart clarifying questions
   - Uses structured output (Pydantic `Clarifications` model)
   - Triggers Temporal workflow update for user interaction

3. **InstructionAgent** (`instruction_agent.py`)
   - Enriches user query with clarification responses
   - Optimizes prompt for deep research model
   - Hands off to existing research pipeline

4. **ResearchManager** (`research_manager.py`)
   - Enhanced to support both direct and interactive flows
   - Manages agent orchestration and state
   - Integrates with Temporal workflow updates

5. **ResearchWorkflow** (`research_bot_workflow.py`)
   - Temporal workflow with interactive capabilities
   - Supports workflow updates for clarification responses
   - Maintains research state throughout interaction

## Usage

### Prerequisites

Before running any workflows, you need to start the Temporal worker:

```bash
# Start the worker in the background
python openai_agents/run_worker.py &
WORKER_PID=$!
echo "Worker started with PID: $WORKER_PID"

# Wait for worker initialization
sleep 5
```

**Important**: The worker must be running for workflows to execute. Keep it running in a separate terminal or background process.

### Basic Research (Original Flow)
```bash
python openai_agents/run_research_workflow.py "Caribbean vacation spots in April"
```

### Interactive Research (With Clarifying Questions)
```bash
python openai_agents/run_research_workflow.py "Inner-north Melbourne food and drink spots" --interactive
```

**New Interactive Experience:**
- Session stays open throughout the research process
- Questions are presented one at a time for natural conversation
- Type answers and press Enter to continue
- Type "exit", "quit", "end", or "done" to terminate early
- Workflow continues running until research is complete

### Check Workflow Status
```bash
python openai_agents/run_research_workflow.py --status --workflow-id research-workflow
```

### Send Clarifications to Running Workflow
```bash
python openai_agents/run_research_workflow.py --clarify question_0="Under $1000" question_1="March 2024"
```

### Interactive Mode
```bash
python openai_agents/run_research_workflow.py
# Will prompt for query and mode selection
```

## Model Configuration

- **Triage & Clarifying Agents**: `gpt-4o-mini` (fast, cost-effective)
- **Instruction Agent**: `gpt-4o-mini` (prompt optimization)
- **Research Pipeline**: Uses existing agents (planner, search, writer)

## Temporal Integration

The workflow uses Temporal's workflow updates to handle interactive clarifications:

- **Query**: `get_status()` - Get current research status
- **Update**: `provide_clarifications()` - Send clarification responses
- **Signal**: `end_workflow()` - End the workflow

## Testing

Run the test suite to validate the implementation:

```bash
python openai_agents/test_enhanced_research.py
```

For usage instructions:
```bash
python openai_agents/test_enhanced_research.py --usage
```

### Cleanup

When finished, stop the worker:

```bash
# If you saved the PID earlier
kill $WORKER_PID 2>/dev/null || true
wait $WORKER_PID 2>/dev/null || true

# Or kill all workers
pkill -f "run_worker.py" || true
```

## Benefits

1. **Smart Questions**: Non-research model generates targeted clarifying questions
2. **Prompt Enrichment**: Enhanced context leads to better research quality
3. **Temporal Native**: Leverages workflow updates for robust interaction handling
4. **Backward Compatible**: Existing simple research flow remains available
5. **Cost Effective**: Uses smaller models for clarification logic

## Files Added/Modified

- **New Files**:
  - `clarifying_agent.py` - Clarifying questions agent
  - `triage_agent.py` - Routing/decision agent  
  - `instruction_agent.py` - Prompt enrichment agent
  - `research_models.py` - Pydantic models for workflow
  - `test_enhanced_research.py` - Test suite

- **Modified Files**:
  - `research_manager.py` - Enhanced with multi-agent flow
  - `research_bot_workflow.py` - Added interactive capabilities
  - `run_research_workflow.py` - Enhanced CLI with clarification support
