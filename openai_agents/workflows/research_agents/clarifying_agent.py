from __future__ import annotations

from typing import List

from pydantic import BaseModel
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import Agent

    from openai_agents.workflows.research_agents.instruction_agent import (
        new_instruction_agent,
    )


class Clarifications(BaseModel):
    """Structured output for clarifying questions"""

    questions: List[str]


CLARIFYING_AGENT_PROMPT = """
If the user hasn't specifically asked for research (unlikely), ask them what research they would like you to do.

GUIDELINES:
1. **Be concise while gathering all necessary information** Ask 2–3 clarifying questions to gather more context for research.
- Make sure to gather all the information needed to carry out the research task in a concise, well-structured manner. Use bullet points or numbered lists if appropriate for clarity. Don't ask for unnecessary information, or information that the user has already provided.
2. **Maintain a Friendly and Non-Condescending Tone**
- For example, instead of saying "I need a bit more detail on Y," say, "Could you share more detail on Y?"
3. **Adhere to Safety Guidelines**
"""


def new_clarifying_agent() -> Agent:
    """Create a new clarifying questions agent"""
    instruction_agent = new_instruction_agent()

    return Agent(
        name="Clarifying Questions Agent",
        model="gpt-4o-mini",
        instructions=CLARIFYING_AGENT_PROMPT,
        output_type=Clarifications,
        handoffs=[instruction_agent],
    )
