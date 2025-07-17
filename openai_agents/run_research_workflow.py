import argparse
import asyncio
import sys

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from openai_agents.workflows.research_bot_workflow import ResearchWorkflow


async def main():
    parser = argparse.ArgumentParser(description="Run basic research workflow")
    parser.add_argument(
        "query",
        nargs="?",
        default="Caribbean vacation spots in April, optimizing for surfing, hiking and water sports",
        help="Research query to execute"
    )
    
    args = parser.parse_args()
    
    # Create client connected to server at the given address
    try:
        client = await Client.connect(
            "localhost:7233",
            data_converter=pydantic_data_converter,
        )
        print(f"🔗 Connected to Temporal server")
    except Exception as e:
        print(f"❌ Failed to connect to Temporal server: {e}")
        print(f"   Make sure Temporal server is running on localhost:7233")
        return

    query = args.query
    print(f"🤖 Starting research: {query}")
    print(f"🔍 Research in progress...")
    print(f"   📋 Planning searches")
    print(f"   🌐 Gathering information")
    print(f"   ✍️  Compiling report")
    print(f"   ⏳ Please wait...")

    # Execute a workflow
    result = await client.execute_workflow(
        ResearchWorkflow.run,
        query,
        id="research-workflow",
        task_queue="openai-agents-task-queue",
    )

    print(f"\n🎉 Research completed!")
    print(f"\n📄 Research Result:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
