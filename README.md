# OpenAI Agents Python SDK Demos

This repository contains four standalone demos showcasing the OpenAI Agents Python SDK integrated with Temporal's durable execution.

See the [Long running agents & human-in-the-loop
](https://openai.github.io/openai-agents-python/running_agents/#long-running-agents-human-in-the-loop) section of the OpenAI's docs for more.

[Watch the demo](https://www.youtube.com/watch?v=fFBZqzT4DD8) to see it in action.

[![Watch the demo](./demo-youtube.jpg)](https://www.youtube.com/watch?v=fFBZqzT4DD8)

For detailed information about the research agents in this repo, see [openai_agents/workflows/research_agents/README.md](openai_agents/workflows/research_agents/README.md)

More Temporal OpenAI Agents SDK samples can be found in Temporal's [samples-python repository](https://github.com/temporalio/samples-python/tree/main/openai_agents).

## Prerequisites

1. **Python 3.10+** - Required for the demos
2. **Temporal Server** - Must be running locally on `localhost:7233`
3. **OpenAI API Key** - Set as environment variable `OPENAI_API_KEY` (note, you will need enough quota on in your [OpenAI account](https://platform.openai.com/api-keys) to run this demo)
4. **PDF Generation Dependencies** - Required for PDF output (optional)

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

### PDF Generation (optional)

Only used in `Demo 4: Multi-Agent Interactive Research Workflow`

For PDF generation functionality, you'll need WeasyPrint and its system dependencies:

#### macOS (using Homebrew)
```bash
brew install weasyprint
# OR install system dependencies for pip installation:
brew install pango glib gtk+3 libffi
```

#### Linux (Ubuntu/Debian)
```bash
# For package installation:
sudo apt install weasyprint

# OR for pip installation:
sudo apt install python3-pip libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```

#### Linux (Fedora)
```bash
# For package installation:
sudo dnf install weasyprint

# OR for pip installation:
sudo dnf install python-pip pango
```

#### Windows
1. Install Python from Microsoft Store
2. Install MSYS2 from https://www.msys2.org/
3. In MSYS2 shell: `pacman -S mingw-w64-x86_64-pango`
4. Set environment variable: `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin`

**Note:** PDF generation gracefully degrades when dependencies are unavailable - workflows will still generate markdown reports.

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

A research system that processes queries and generates comprehensive markdown reports.

**Files:**
- `openai_agents/workflows/research_bot_workflow.py` - Main research workflow
- `openai_agents/workflows/simple_research_manager.py` - Simple research orchestrator
- `openai_agents/workflows/research_agents/` - Shared research agent components
- `openai_agents/run_research_workflow.py` - Research client

**Agents:**
- **Planner Agent**: Plans web searches based on the query
- **Search Agent**: Performs searches to gather information
- **Writer Agent**: Compiles the final research report

**To run:**
```bash
uv run openai_agents/run_research_workflow.py "Tell me about quantum computing"
```

**Output:**
- `research_report.md` - Comprehensive markdown report

**Note:** The research workflow may take 1-2 minutes to complete due to web searches and report generation.

### Demo 4: Multi-Agent Interactive Research Workflow

An enhanced version of the research workflow with interactive clarifying questions to refine research parameters before execution, AI-generated hero images, and optional PDF generation.

This example is designed to be similar to the OpenAI Cookbook: [Introduction to deep research in the OpenAI API](https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api)

**Files:**
- `openai_agents/workflows/interactive_research_workflow.py` - Interactive research workflow
- `openai_agents/workflows/research_agents/` - All research agent components
- `openai_agents/run_interactive_research_workflow.py` - Interactive research client
- `openai_agents/workflows/pdf_generation_activity.py` - PDF generation activity
- `openai_agents/workflows/image_generation_activity.py` - Image generation activity
- `openai_agents/workflows/research_agents/pdf_generator_agent.py` - PDF generation agent
- `openai_agents/workflows/research_agents/imagegen_agent.py` - Image generation agent

**Agents:**
- **Triage Agent**: Analyzes research queries and determines if clarifications are needed
- **Clarifying Agent**: Generates follow-up questions for better research parameters
- **Instruction Agent**: Refines research parameters based on user responses
- **Planner Agent**: Creates web search plans
- **Search Agent**: Performs web searches
- **Writer Agent**: Compiles final research reports
- **ImageGen Agent**: Generates contextual hero images for reports (runs in parallel with research)
- **PDF Generator Agent**: Converts markdown reports to professionally formatted PDFs with embedded images

**To run:**
```bash
uv run openai_agents/run_interactive_research_workflow.py "Tell me about quantum computing"
```

**Additional options:**
- `--workflow-id`: Specify custom workflow ID
- `--new-session`: Force start a new workflow session
- `--status`: Get status of existing workflow
- `--clarify`: Send clarification responses

**Output:**
- `research_report.md` - Comprehensive markdown report
- `pdf_output/research_report.pdf` - Professionally formatted PDF with AI-generated hero image (if PDF generation is available)
- `temp_images/` - Generated hero images

**Image Generation Requirements:**
Image generation requires an OpenAI account with a verified organization. If your organization is not verified, image generation will silently fail and PDFs will be generated without hero images. To verify your organization, visit https://platform.openai.com/settings/organization/general and click "Verify Organization".

**Note:** The interactive workflow may take 2-3 minutes to complete due to web searches, image generation, and report compilation.

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
│   ├── run_interactive_research_workflow.py     # Interactive research demo runner
│   └── workflows/
│       ├── __init__.py
│       ├── hello_world_workflow.py     # Simple haiku agent
│       ├── tools_workflow.py           # Weather tool demo
│       ├── get_weather_activity.py     # Weather activity
│       ├── research_bot_workflow.py    # Main research workflow
│       ├── interactive_research_workflow.py  # Interactive research workflow
│       ├── pdf_generation_activity.py  # PDF generation activity
│       ├── image_generation_activity.py # Image generation activity
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
│           ├── writer_agent.py         # Report writing agent
│           ├── imagegen_agent.py       # Image generation agent
│           └── pdf_generator_agent.py  # PDF generation agent
```

## Development

### Code Quality Tools

```bash
# Format code
uv run -m black .
uv run -m isort .

# Type checking
uv run -m mypy --check-untyped-defs --namespace-packages .
uv run pyright .
```

## Key Features

- **Temporal Workflows**: All demos use Temporal for reliable workflow orchestration
- **OpenAI Agents**: Powered by the OpenAI Agents SDK for natural language processing
- **Multi-Agent Systems**: The research demo showcases complex multi-agent coordination
- **Interactive Workflows**: Research demo supports real-time user interaction
- **Tool Integration**: Tools demo shows how to integrate external activities
- **PDF Generation**: Interactive research workflow generates professional PDF reports alongside markdown

## License

MIT License - see the original project for full license details.