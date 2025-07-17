# Research Agent Components

This directory contains shared agent components used by two distinct research workflows in this demo project. The agents demonstrate different patterns of orchestration, from simple linear execution to complex multi-agent interactions with user clarifications.

## Two Research Workflows

This project includes two research workflows that showcase different levels of complexity:

### Basic Research Workflow
- **File**: `../research_bot_workflow.py`
- **Manager**: `../simple_research_manager.py` (SimpleResearchManager)
- **Purpose**: Demonstrates simple agent orchestration in a linear pipeline
- **Usage**: `uv run openai_agents/run_research_workflow.py "your research query"`

### Interactive Research Workflow  
- **File**: `../interactive_research_workflow.py`
- **Manager**: `research_manager.py` (InteractiveResearchManager)
- **Purpose**: Advanced workflow with intelligent question generation and user interaction
- **Usage**: `uv run openai_agents/run_interactive_research_workflow.py "your research query"`

The interactive workflow is based on patterns from the [OpenAI Deep Research API cookbook](https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api_agents).

## Basic Research Flow

```
User Query → Planner Agent → Search Agent(s) → Writer Agent → Final Report
              (gpt-4o)        (parallel)       (gpt-4o)
```

### Agent Roles in Basic Flow:

**Planner Agent** (`planner_agent.py`)
- Analyzes the user query and generates 5-20 strategic web search terms
- Uses GPT-4o for comprehensive search planning
- Outputs structured `WebSearchPlan` with search terms and reasoning

**Search Agent** (`search_agent.py`) 
- Executes multiple web searches in parallel using the search plan
- Each search includes the query term and reasoning for context
- Handles search failures gracefully and returns consolidated results

**Writer Agent** (`writer_agent.py`)
- Compiles all search results into a comprehensive markdown report
- Synthesizes information from multiple sources
- Structures the final output as a cohesive research document

## Interactive Research Flow

```
User Query → Triage Agent → Decision
             (gpt-4o-mini)     ↓
                        Clarification Needed?
                               ↓
           ┌─── Yes: Clarifying Agent → Questions → User Input
           │        (gpt-4o-mini)         ↓
           │                     Instruction Agent → Enriched Query
           │                     (gpt-4o-mini)        ↓
           └─── No: Instruction Agent → Direct Research
                    (gpt-4o-mini)           ↓
                                    Planner Agent → Search Agent(s) → Writer Agent
                                    (gpt-4o)        (parallel)       (gpt-4o)
                                           ↓
                                    Final Report
```

### Agent Roles in Interactive Flow:

**Triage Agent** (`triage_agent.py`)
- Analyzes query specificity and determines if clarifications are needed
- Routes to either clarifying questions or direct research
- Uses GPT-4o-mini for fast, cost-effective decision making
- Looks for vague terms, missing context, or broad requests

**Clarifying Agent** (`clarifying_agent.py`)  
- Generates 2-3 targeted questions to gather missing information
- Focuses on preferences, constraints, and specific requirements
- Uses structured output (`Clarifications` model) for consistent formatting
- Triggers Temporal workflow updates for user interaction

**Instruction Agent** (`instruction_agent.py`)
- Enriches the original query with user responses to clarifying questions
- Optimizes the enhanced query for the research pipeline
- Processes specific queries that don't need clarifications
- Prepares refined input for the planner agent

**Planner Agent** - Same as basic flow
**Search Agent** - Same as basic flow  
**Writer Agent** - Same as basic flow

## Shared Agent Components

All agents in this directory are used by one or both research workflows:

- **`planner_agent.py`** - Web search planning (used by both workflows)
- **`search_agent.py`** - Web search execution (used by both workflows)
- **`writer_agent.py`** - Report generation (used by both workflows)
- **`triage_agent.py`** - Query analysis and routing (interactive workflow only)
- **`clarifying_agent.py`** - Question generation (interactive workflow only)
- **`instruction_agent.py`** - Query enrichment (interactive workflow only)
- **`research_models.py`** - Pydantic models for workflow state (interactive workflow only)
- **`research_manager.py`** - InteractiveResearchManager orchestration

## Usage Examples

### Running Basic Research
```bash
# Start worker first
uv run openai_agents/run_worker.py &

# Run basic research
uv run openai_agents/run_research_workflow.py "Best sustainable energy solutions for small businesses"
```

### Running Interactive Research
```bash
# Start worker first  
uv run openai_agents/run_worker.py &

# Run interactive research
uv run openai_agents/run_interactive_research_workflow.py "Travel recommendations for Japan"
```

The interactive workflow will ask clarifying questions like:
- What's your budget range?
- When are you planning to travel?
- What type of activities interest you most?
- Any dietary restrictions or accessibility needs?

## Model Configuration

**Cost-Optimized Models:**
- **Triage Agent**: `gpt-4o-mini` - Fast routing decisions
- **Clarifying Agent**: `gpt-4o-mini` - Question generation  
- **Instruction Agent**: `gpt-4o-mini` - Query enrichment

**Research Models:**
- **Planner Agent**: `gpt-4o` - Complex search strategy
- **Search Agent**: Uses web search APIs (no LLM)
- **Writer Agent**: `gpt-4o` - High-quality report synthesis

This configuration balances cost efficiency for routing/clarification logic while using more powerful models for core research tasks.