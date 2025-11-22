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
- Uses `gpt-5` model for high-quality report synthesis
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
                │                                                             ├──→ ImageGen Agent (gpt-4o-mini) ──┐
                │                                                             │         (runs in parallel)         │
                │                                                             │                                    │
                │                                                             └──→ Planner Agent (gpt-4o)         │
                │                                                                          ├──→ Search Agent(s)    │
                │                                                                          └──→ Writer Agent       │
                │                                                                                     │            │
                │                                                                                     └────────────┴──→ PDF Generator Agent
                │                                                                                                              └──→ Report + PDF (with image)
                │
                └── No → Instruction Agent (gpt-4o-mini)
                               └──→ Direct Research
                                          │
                                          ├──→ ImageGen Agent (gpt-4o-mini) ──┐
                                          │         (runs in parallel)         │
                                          │                                    │
                                          └──→ Planner Agent (gpt-4o)         │
                                                       ├──→ Search Agent(s)    │
                                                       └──→ Writer Agent       │
                                                                  │            │
                                                                  └────────────┴──→ PDF Generator Agent
                                                                                           └──→ Report + PDF (with image)
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

**ImageGen Agent** (`imagegen_agent.py`)
- Uses `gpt-4o-mini` model for fast, cost-effective image description generation
- Generates compelling 2-sentence descriptions that capture the research topic essence
- Calls the `generate_image` activity (using OpenAI's image generation API) to create contextual hero images
- Runs in parallel with the entire research pipeline (planning, searching, writing) for maximum efficiency
- Returns structured output (`ImageGenData`) including:
  - `success`: Boolean indicating generation status
  - `image_description`: The 2-sentence description used for generation
  - `image_file_path`: Path to generated image file in `temp_images/` directory
  - `error_message`: Detailed error information (if failed)
- Graceful error handling for non-retryable failures (API quota, organization verification, serialization errors)
- Images are embedded as hero images in PDF reports under the document title

**Organization Verification Requirement:**
Image generation requires an OpenAI account with a verified organization. If you encounter a 403 error like:
```
Error code: 403 - {'error': {'message': 'Your organization must be verified to use the model...
```

This means your organization needs verification. The workflow will continue without images and log:
```
Non-retryable image generation error: Error code: 403... Continuing without image.
```

**To fix:** Visit https://platform.openai.com/settings/organization/general and complete the "Verify Organization" process. Image generation will work on the next workflow run.

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
- Embeds hero images under the document title
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
- **`imagegen_agent.py`** - Hero image generation (interactive workflow only)
- **`pdf_generator_agent.py`** - PDF generation with image embedding (interactive workflow only)
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
- **ImageGen Agent**: `gpt-4o-mini` - Image description generation

**Research Models:**
- **Planner Agent**: `gpt-4o` - Complex search strategy
- **Search Agent**: `gpt-4o-mini` - Web search with required tool usage
- **Writer Agent**: `gpt-5` - High-quality report synthesis
- **PDF Generator Agent**: `gpt-4o-mini` - PDF formatting decisions + WeasyPrint for generation

This configuration balances cost efficiency for routing/clarification/image generation logic while using more powerful models for core research tasks. The ImageGen Agent runs in parallel with the research pipeline to maximize throughput.

## Future Work

### Distributed Worker Compatibility

Currently, the image generation feature writes generated images to the local file system (`temp_images/` directory). This means the workflow is **not compatible with workers running on different hosts** - the PDF Generator Agent must run on the same host as the ImageGen Agent to access the generated image files.

**Limitation:** In a distributed Temporal deployment where activities may execute on different worker hosts, the PDF generation activity may not be able to read the image file created by the image generation activity.

**Potential Solutions:**
- Store images in cloud object storage (S3, GCS, etc.) instead of local filesystem
- Use Temporal's blob storage capabilities to pass image data between activities
- Implement a shared network filesystem accessible by all workers
- Return base64-encoded image data (requires addressing serialization size limits)