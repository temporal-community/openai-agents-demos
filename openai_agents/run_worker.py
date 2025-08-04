from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("openai.agents").setLevel(logging.CRITICAL)

from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters

from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from openai_agents.workflows.get_weather_activity import get_weather
from openai_agents.workflows.hello_world_workflow import HelloWorldAgent
from openai_agents.workflows.interactive_research_workflow import (
    InteractiveResearchWorkflow,
)
from openai_agents.workflows.pdf_generation_activity import generate_pdf
from openai_agents.workflows.research_bot_workflow import ResearchWorkflow
from openai_agents.workflows.tools_workflow import ToolsWorkflow


async def main():
    logging.basicConfig(level=logging.INFO)

    # Create client connected to server at the given address
    client = await Client.connect(
        "localhost:7233",
        plugins=[
            OpenAIAgentsPlugin(
                model_params=ModelActivityParameters(
                    start_to_close_timeout=timedelta(seconds=35),
                    schedule_to_close_timeout=timedelta(seconds=300),
                    retry_policy=RetryPolicy(
                        backoff_coefficient=2.0,
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=5),
                    ),
                )
            ),
        ],
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
            get_weather,
            generate_pdf,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
