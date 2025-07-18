from __future__ import annotations

import asyncio
import logging
import warnings
from datetime import timedelta

logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("openai.agents").setLevel(logging.CRITICAL)

from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivity,
    ModelActivityParameters,
    set_open_ai_agent_temporal_overrides,
)
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from openai_agents.workflows.get_weather_activity import get_weather
from openai_agents.workflows.pdf_generation_activity import generate_pdf
from openai_agents.workflows.hello_world_workflow import HelloWorldAgent
from openai_agents.workflows.interactive_research_workflow import (
    InteractiveResearchWorkflow,
)
from openai_agents.workflows.research_bot_workflow import ResearchWorkflow
from openai_agents.workflows.tools_workflow import ToolsWorkflow


async def main():
    logging.basicConfig(level=logging.INFO)
    
    with set_open_ai_agent_temporal_overrides(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        ),
    ):
        # Create client connected to server at the given address
        client = await Client.connect(
            "localhost:7233",
            data_converter=pydantic_data_converter,
        )

        worker = Worker(
            client,
            task_queue="openai-agents-task-queue",
            workflows=[
                HelloWorldAgent,
                ToolsWorkflow,
                ResearchWorkflow,
                InteractiveResearchWorkflow,
            ],
            activities=[
                ModelActivity().invoke_model_activity,
                get_weather,
                generate_pdf,
            ],
        )
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
