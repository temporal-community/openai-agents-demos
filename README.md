# OpenAI Agents Python SDK Demos

This repository contains four standalone demos showcasing the OpenAI Agents Python SDK integrated with Temporal's durable execution.

## Prerequisites

1. **Python 3.10+** - Required for the demos
2. **Temporal Server** - Must be running locally on `localhost:7233`
3. **OpenAI API Key** - Set as environment variable `OPENAI_API_KEY`

### Starting Temporal Server

```bash
# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh

# Start Temporal server
temporal server start-dev
```

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Running the Demos

### Step 1: Start the Worker

In one terminal, start the worker that will handle all workflows:

```bash
uv run openai_agents/run_worker.py
```

Keep this running throughout your demo sessions. The worker registers all available workflows and activities.

### Step 2: Run Any Demo

In a separate terminal, run any of the demo scripts:

### Demo 1: Hello World Workflow

A simple agent that responds only in haikus.

**Files:**
- `openai_agents/workflows/hello_world_workflow.py` - Simple haiku-generating agent
- `openai_agents/run_hello_world_workflow.py` - Client runner

**To run:**
```bash
uv run openai_agents/run_hello_world_workflow.py
```

### Demo 2: Tools Workflow

An agent that uses a weather activity as a tool.

**Files:**
- `openai_agents/workflows/tools_workflow.py` - Workflow using weather tool
- `openai_agents/workflows/get_weather_activity.py` - Weather activity
- `openai_agents/run_tools_workflow.py` - Client runner

**To run:**
```bash
uv run openai_agents/run_tools_workflow.py
```

### Demo 3: Basic Research Workflow

A research system that processes queries and generates comprehensive reports.

**Files:**
- `openai_agents/workflows/research_bot_workflow.py` - Main research workflow
- `openai_agents/workflows/research_agents/` - All research agent components
- `openai_agents/run_research_workflow.py` - Research client

**Agents:**
- **Planner Agent**: Plans web searches based on the query
- **Search Agent**: Performs searches to gather information
- **Writer Agent**: Compiles the final research report

**To run:**
```bash
uv run openai_agents/run_research_workflow.py "Tell me about quantum computing"
```

**Note:** The research workflow may take 2-3 minutes to complete due to web searches and report generation.

### Demo 4: Multi-Agent Interactive Research Workflow

An enhanced version of the research workflow with interactive clarifying questions to refine research parameters before execution.

This example is designed to be similar to the OpenAI Cookbook: [Introduction to deep research in the OpenAI API](https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api)

**Files:**
- `openai_agents/workflows/interactive_research_workflow.py` - Interactive research workflow
- `openai_agents/workflows/research_agents/` - All research agent components
- `openai_agents/run_interactive_research.py` - Interactive research client

**Agents:**
- **Triage Agent**: Analyzes research queries and determines if clarifications are needed
- **Clarifying Agent**: Generates follow-up questions for better research parameters
- **Instruction Agent**: Refines research parameters based on user responses
- **Planner Agent**: Creates web search plans
- **Search Agent**: Performs web searches
- **Writer Agent**: Compiles final research reports

**To run:**
```bash
uv run openai_agents/run_interactive_research.py "Tell me about quantum computing"
```

**Additional options:**
- `--workflow-id`: Specify custom workflow ID
- `--new-session`: Force start a new workflow session
- `--status`: Get status of existing workflow
- `--clarify`: Send clarification responses

**Note:** The interactive workflow may take 2-3 minutes to complete due to web searches and report generation.

## Project Structure

```
openai-agents-demos/
├── README.md                           # This file
├── pyproject.toml                      # Project dependencies
├── openai_agents/
│   ├── __init__.py
│   ├── README.md                       # Original documentation
│   ├── run_worker.py                   # Worker that registers all workflows
│   ├── run_hello_world_workflow.py     # Hello World demo runner
│   ├── run_tools_workflow.py           # Tools demo runner
│   ├── run_research_workflow.py        # Research demo runner
│   ├── run_interactive_research.py     # Interactive research demo runner
│   └── workflows/
│       ├── __init__.py
│       ├── hello_world_workflow.py     # Simple haiku agent
│       ├── tools_workflow.py           # Weather tool demo
│       ├── get_weather_activity.py     # Weather activity
│       ├── research_bot_workflow.py    # Main research workflow
│       ├── interactive_research_workflow.py  # Interactive research workflow
│       └── research_agents/            # Research agent components
│           ├── __init__.py
│           ├── README.md               # Research agents documentation
│           ├── research_models.py      # Data models
│           ├── research_manager.py     # Main research orchestrator
│           ├── triage_agent.py         # Query analysis agent
│           ├── clarifying_agent.py     # Question generation agent
│           ├── instruction_agent.py    # Research instruction agent
│           ├── planner_agent.py        # Research planning agent
│           ├── search_agent.py         # Web search agent
│           └── writer_agent.py         # Report writing agent
```

## Key Features

- **Temporal Workflows**: All demos use Temporal for reliable workflow orchestration
- **OpenAI Agents**: Powered by the OpenAI Agents SDK for natural language processing
- **Multi-Agent Systems**: The research demo showcases complex multi-agent coordination
- **Interactive Workflows**: Research demo supports real-time user interaction
- **Tool Integration**: Tools demo shows how to integrate external activities

## License

MIT License - see the original project for full license details.