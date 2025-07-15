import asyncio
import argparse
import sys
from typing import Dict, List

from temporalio.client import Client, WorkflowHandle
from temporalio.contrib.pydantic import pydantic_data_converter

from openai_agents.workflows.research_bot_workflow import ResearchWorkflow
from openai_agents.workflows.research_agents.research_models import (
    ClarificationInput,
    SingleClarificationInput,
    UserQueryInput,
    ResearchInteraction,
)


async def run_basic_research(client: Client, query: str, workflow_id: str):
    """Run basic research without clarifications"""
    print(f"🔍 Starting basic research: {query}")
    
    result = await client.execute_workflow(
        ResearchWorkflow.run,
        args=[query, False],  # query, use_clarifications=False
        id=workflow_id,
        task_queue="openai-agents-task-queue",
    )
    
    print(f"\n📄 Research Result:")
    print("=" * 60)
    print(result)
    return result


async def run_interactive_research_wealth_pattern(client: Client, query: str, workflow_id: str):
    """Run interactive research following the wealth management pattern"""
    print(f"🤖 Starting interactive research: {query}")
    
    # Check if workflow exists and is running
    handle = None
    start_new = True
    
    try:
        handle = client.get_workflow_handle(workflow_id)
        print("Checking if workflow is already running...")
        
        # Try to get the status to see if it's still running
        try:
            status = await handle.query(ResearchWorkflow.get_status)
            if status and status.status not in ["completed"]:
                print("Found existing running workflow, using it...")
                start_new = False
            else:
                print("Existing workflow is completed, will start new one...")
        except Exception as query_error:
            print(f"Error querying workflow (likely completed): {query_error}")
            print("Will start a new workflow...")
            
    except Exception as handle_error:
        print(f"Workflow not found: {handle_error}")
        print("Will start a new workflow...")
    
    if start_new:
        # Use a unique workflow ID to avoid conflicts
        import time
        unique_id = f"{workflow_id}-{int(time.time())}"
        print(f"Starting new research workflow: {unique_id}")
        
        try:
            handle = await client.start_workflow(
                ResearchWorkflow.run,
                args=[None, False],  # No initial query, we'll send it via update
                id=unique_id,
                task_queue="openai-agents-task-queue",
            )
        except Exception as start_error:
            print(f"❌ Failed to start workflow: {start_error}")
            print("💡 Try using the --new-session flag to force a new session")
            raise
    
    if not handle:
        raise RuntimeError("Failed to get workflow handle")
        
    # Start the research process
    print(f"🔄 Initiating research for: {query}")
    await handle.execute_update(
        ResearchWorkflow.start_research,
        UserQueryInput(query=query)
    )
    
    # Interactive loop - like wealth management
    while True:
        try:
            status = await handle.query(ResearchWorkflow.get_status)
            
            if not status:
                await asyncio.sleep(1)
                continue
            
            if status.status == "awaiting_clarifications":
                print(f"\n❓ I need to ask you some clarifying questions to provide better research.")
                print("-" * 60)
                
                # Show first question
                current_question = status.get_current_question()
                if current_question:
                    print(f"Question {status.current_question_index + 1} of {len(status.clarification_questions or [])}")
                    print(f"{current_question}")
                    
                    answer = input("Your answer: ").strip()
                    
                    if answer.lower() in ["exit", "quit", "end", "done"]:
                        print("Ending research session...")
                        await handle.signal(ResearchWorkflow.end_workflow_signal)
                        break
                    
                    # Send single answer
                    await handle.execute_update(
                        ResearchWorkflow.provide_single_clarification,
                        SingleClarificationInput(
                            question_index=status.current_question_index,
                            answer=answer or "No specific preference"
                        )
                    )
                    
            elif status.status == "collecting_answers":
                # Get next question
                current_question = status.get_current_question()
                if current_question:
                    print(f"\nQuestion {status.current_question_index + 1} of {len(status.clarification_questions or [])}")
                    print(f"{current_question}")
                    
                    answer = input("Your answer: ").strip()
                    
                    if answer.lower() in ["exit", "quit", "end", "done"]:
                        print("Ending research session...")
                        await handle.signal(ResearchWorkflow.end_workflow_signal)
                        break
                    
                    # Send single answer
                    await handle.execute_update(
                        ResearchWorkflow.provide_single_clarification,
                        SingleClarificationInput(
                            question_index=status.current_question_index,
                            answer=answer or "No specific preference"
                        )
                    )
                    
            elif status.status == "researching":
                print("🔍 Conducting research with your preferences...")
                await asyncio.sleep(3)  # Give it time to research
                
            elif status.status == "completed":
                print(f"\n🎉 Research completed!")
                result = await handle.result()
                print(f"\n📄 Research Result:")
                print("=" * 60)
                print(result)
                return result
                
            elif status.status == "pending":
                print("⏳ Starting research...")
                await asyncio.sleep(2)
                
            else:
                print(f"📊 Status: {status.status}")
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Error during interaction: {e}")
            await asyncio.sleep(2)

# Keep the old function for backward compatibility
async def run_interactive_research(client: Client, query: str, workflow_id: str):
    """Legacy interactive research - redirects to new pattern"""
    return await run_interactive_research_wealth_pattern(client, query, workflow_id)


async def get_workflow_status(client: Client, workflow_id: str):
    """Get the status of an existing workflow"""
    try:
        handle = client.get_workflow_handle(workflow_id)
        status = await handle.query(ResearchWorkflow.get_status)
        
        if status:
            print(f"📊 Workflow {workflow_id} status: {status.status}")
            if status.clarification_questions:
                print(f"❓ Pending questions: {len(status.clarification_questions)}")
            if status.final_result:
                print(f"✅ Has final result")
        else:
            print(f"❌ No status available for workflow {workflow_id}")
            
    except Exception as e:
        print(f"❌ Error getting workflow status: {e}")


async def send_clarifications(client: Client, workflow_id: str, responses: Dict[str, str]):
    """Send clarification responses to an existing workflow"""
    try:
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.execute_update(
            ResearchWorkflow.provide_clarifications,
            ClarificationInput(responses=responses)
        )
        print(f"✅ Clarifications sent to workflow {workflow_id}")
        print(f"📊 Updated status: {result.status}")
        
    except Exception as e:
        print(f"❌ Error sending clarifications: {e}")


def parse_clarifications(clarification_args: List[str]) -> Dict[str, str]:
    """Parse clarification responses from command line arguments"""
    responses = {}
    for arg in clarification_args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            responses[key] = value
    return responses


async def main():
    parser = argparse.ArgumentParser(description="OpenAI Research Workflow CLI")
    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Use interactive mode with clarifying questions")
    parser.add_argument("--workflow-id", default="research-workflow", 
                       help="Workflow ID (default: research-workflow)")
    parser.add_argument("--new-session", action="store_true",
                       help="Force start a new workflow session (with unique ID)")
    parser.add_argument("--status", action="store_true",
                       help="Get status of existing workflow")
    parser.add_argument("--clarify", nargs="+", metavar="KEY=VALUE",
                       help="Send clarification responses (e.g., --clarify question_0='travel budget' question_1='March')")
    
    args = parser.parse_args()
    
    # Create client
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
    
    # Handle different modes
    if args.status:
        await get_workflow_status(client, args.workflow_id)
        
    elif args.clarify:
        responses = parse_clarifications(args.clarify)
        await send_clarifications(client, args.workflow_id, responses)
        
    elif args.query:
        # Handle new session flag
        workflow_id = args.workflow_id
        if args.new_session:
            import time
            workflow_id = f"{args.workflow_id}-{int(time.time())}"
            print(f"🆕 Using new session ID: {workflow_id}")
            
        if args.interactive:
            await run_interactive_research(client, args.query, workflow_id)
        else:
            await run_basic_research(client, args.query, workflow_id)
            
    else:
        # Interactive query input
        print("🔍 OpenAI Research Workflow")
        print("=" * 40)
        query = input("Enter your research query: ").strip()
        
        if not query:
            print("❌ Query cannot be empty")
            return
            
        mode = input("Use clarifying questions? (y/n, default=n): ").strip().lower()
        use_interactive = mode == 'y'
        
        if use_interactive:
            await run_interactive_research(client, query, args.workflow_id)
        else:
            await run_basic_research(client, query, args.workflow_id)


if __name__ == "__main__":
    asyncio.run(main())
