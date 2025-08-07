import asyncio
import sys

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from openai_agents.workflows.hello_world_workflow import HelloWorldAgent


async def main():
    # Get the input string from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_hello_world_workflow.py <input_string>")
        sys.exit(1)
    input_string = sys.argv[1]

    # Create client connected to server at the given address
    client = await Client.connect(
        "localhost:7233",
        data_converter=pydantic_data_converter,
    )

    # Execute a workflow
    result = await client.execute_workflow(
        HelloWorldAgent.run,
        input_string,
        id="my-workflow-id",
        task_queue="openai-agents-task-queue",
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
