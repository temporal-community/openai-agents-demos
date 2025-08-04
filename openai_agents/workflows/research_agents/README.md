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
User Query → Planner Agent → Search Agent(s) → Writer Agent → Markdown Report
              (gpt-4o)        (parallel)       (gpt-4o)
```

### Agent Roles in Basic Flow:

**Planner Agent** (`planner_agent.py`)
- Analyzes the user query and generates 5-20 strategic web search terms
- Uses `gpt-4o` for comprehensive search planning
- Outputs structured `WebSearchPlan` with search terms and reasoning
- Each search item includes `reason` (justification) and `query` (search term)

**Search Agent** (`search_agent.py`)
- Executes web searches using `WebSearchTool()` with required tool usage
- Produces 2-3 paragraph summaries (max 300 words) per search
- Focuses on capturing main points concisely for report synthesis
- Handles search failures gracefully and returns consolidated results
- Uses no LLM model directly - just processes search tool results

**Writer Agent** (`writer_agent.py`)
- Uses `o3-mini` model for high-quality report synthesis
- Generates comprehensive 5-10 page reports (800-2000 words)
- Returns structured `ReportData` with:
  - `short_summary`: 2-3 sentence overview
  - `markdown_report`: Full detailed report
  - `follow_up_questions`: Suggested research topics
- Creates detailed sections with analysis, examples, and conclusions

## Interactive Research Flow

```
User Query
    └──→ Triage Agent (gpt-4o-mini)
              └──→ Decision: Clarification Needed?
                            │
                ├── Yes → Clarifying Agent (gpt-4o-mini)
                │             └──→ Generate Questions
                │                          └──→ User Input
                │                                     └──→ Instruction Agent (gpt-4o-mini)
                │                                                   └──→ Enriched Query
                │                                                             │
                │                                                             └──→ Planner Agent (gpt-4o)
                │                                                                          ├──→ Search Agent(s) (parallel)
                │                                                                          └──→ Writer Agent (o3-mini)
                │                                                                                     └──→ PDF Generator Agent
                │                                                                                                └──→ Report + PDF
                │
                └── No → Instruction Agent (gpt-4o-mini)
                               └──→ Direct Research
                                          └──→ Planner Agent (gpt-4o)
                                                       ├──→ Search Agent(s) (parallel)
                                                       └──→ Writer Agent (o3-mini)
                                                                     └──→ PDF Generator Agent
                                                                                └──→ Report + PDF
```

### Agent Roles in Interactive Flow:

**Triage Agent** (`triage_agent.py`)
- Analyzes query specificity and determines if clarifications are needed
- Routes to either clarifying questions or direct research using agent handoffs
- Uses `gpt-4o-mini` for fast, cost-effective decision making
- Looks for vague terms, missing context, or broad requests
- Can handoff to either `new_clarifying_agent()` or `new_instruction_agent()`

**Clarifying Agent** (`clarifying_agent.py`)
- Uses `gpt-4o-mini` model for question generation
- Generates 2-3 targeted questions to gather missing information
- Focuses on preferences, constraints, and specific requirements
- Returns structured output (`Clarifications` model with `questions` list)
- Can handoff to `new_instruction_agent()` after collecting questions
- Integrates with Temporal workflow updates for user interaction

**Instruction Agent** (`instruction_agent.py`)
- Uses `gpt-4o-mini` model for query enhancement
- Enriches original query with user responses to clarifying questions
- Processes specific queries that don't need clarifications
- Rewrites queries into detailed research instructions using first-person perspective
- Can handoff to `new_planner_agent()` with enriched query
- Handles language preferences and output formatting requirements

**PDF Generator Agent** (`pdf_generator_agent.py`)
- Uses `gpt-4o-mini` for intelligent formatting analysis and styling decisions
- Calls the `generate_pdf` activity with 30-second timeout for actual PDF creation
- Returns structured output (`PDFReportData`) including:
  - `success`: Boolean indicating generation status
  - `formatting_notes`: AI-generated notes about styling decisions
  - `pdf_file_path`: Path to generated PDF file (if successful)
  - `error_message`: Detailed error information (if failed)
- Graceful error handling with detailed feedback
- Professional PDF styling with proper typography and layout
- Files saved to `pdf_output/` directory with timestamped names

## Agent Handoff Pattern

The research agents use OpenAI's agent handoff pattern to chain execution seamlessly:

- **Triage Agent** → Can handoff to either **Clarifying Agent** or **Instruction Agent**
- **Clarifying Agent** → Handoffs to **Instruction Agent** after collecting questions
- **Instruction Agent** → Handoffs to **Planner Agent** with enriched query
- **Other agents** → Execute independently without handoffs (Planner, Search, Writer, PDF Generator)

This pattern allows complex multi-agent workflows where one agent can automatically transfer control to the next appropriate agent in the pipeline, enabling sophisticated research orchestration with minimal coordination overhead.

## Shared Agent Components

All agents in this directory are used by one or both research workflows:

- **`planner_agent.py`** - Web search planning (used by both workflows)
- **`search_agent.py`** - Web search execution (used by both workflows)
- **`writer_agent.py`** - Report generation (used by both workflows)
- **`pdf_generator_agent.py`** - PDF generation (interactive workflow only)
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
- **Writer Agent**: `o3-mini` - High-quality report synthesis
- **PDF Generator Agent**: `gpt-4o-mini` - PDF formatting decisions + WeasyPrint for generation

This configuration balances cost efficiency for routing/clarification logic while using more powerful models for core research tasks.