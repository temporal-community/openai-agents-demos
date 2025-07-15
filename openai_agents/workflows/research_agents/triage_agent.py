from __future__ import annotations

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import Agent

    from openai_agents.workflows.research_agents.clarifying_agent import new_clarifying_agent
    from openai_agents.workflows.research_agents.instruction_agent import new_instruction_agent


TRIAGE_AGENT_PROMPT = """
You are a triage agent that determines if a research query needs clarifying questions to provide better results.

Analyze the user's query and decide:

**Route to CLARIFYING AGENT if the query:**
- Lacks specific details about preferences (budget, timing, style, etc.)
- Is too broad (like "best restaurants" without location/cuisine preferences)
- Would benefit from understanding user's specific needs or constraints
- Contains vague terms like "best", "good", "nice" without criteria

**Route to INSTRUCTION AGENT if the query:**
- Is already very specific with clear parameters
- Contains detailed criteria and constraints
- Is a factual lookup that doesn't need user preferences
- Has sufficient context to conduct focused research

For the query "Inner-north Melbourne food and drink spots" - this is broad and would benefit from clarifying:
- Budget range
- Cuisine preferences  
- Dining occasion (casual/formal)
- Specific neighborhoods in inner-north
- Dietary restrictions

**Always prefer clarifying questions for location-based queries without specific criteria.**

• If clarifications needed → call transfer_to_clarifying_questions_agent
• If specific enough → call transfer_to_research_instruction_agent

Return exactly ONE function-call.
"""


def new_triage_agent() -> Agent:
    """Create a new triage agent for routing research requests"""
    clarifying_agent = new_clarifying_agent()
    instruction_agent = new_instruction_agent()
    
    return Agent(
        name="Triage Agent",
        model="gpt-4o-mini",
        instructions=TRIAGE_AGENT_PROMPT,
        handoffs=[clarifying_agent, instruction_agent],
    )