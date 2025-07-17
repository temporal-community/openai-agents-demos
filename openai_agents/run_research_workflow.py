import argparse
import asyncio
from pathlib import Path

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
    print(f"   📑 Generating PDF")
    print(f"   ⏳ Please wait...")

    # Execute a workflow
    result = await client.execute_workflow(
        ResearchWorkflow.run,
        query,
        id="research-workflow",
        task_queue="openai-agents-task-queue",
    )

    print(f"\n🎉 Research completed!")
    
    # Save markdown report
    markdown_file = Path("research_report.md")
    markdown_file.write_text(result.markdown_report)
    print(f"📄 Markdown report saved to: {markdown_file}")
    
    # Save PDF report if available
    if result.pdf_file_path:
        import shutil
        # Create pdf_output directory if it doesn't exist
        pdf_output_dir = Path("pdf_output")
        pdf_output_dir.mkdir(exist_ok=True)
        
        # Copy to both the pdf_output directory and current directory
        pdf_file = Path("research_report.pdf")
        shutil.copy2(result.pdf_file_path, pdf_file)
        
        # Also copy to pdf_output with original name
        final_pdf = pdf_output_dir / "research_report.pdf"
        shutil.copy2(result.pdf_file_path, final_pdf)
        
        print(f"📑 PDF report saved to: {pdf_file}")
        print(f"📑 PDF also saved to: {final_pdf}")
    else:
        print(f"⚠️  PDF generation not available (continuing with markdown only)")
    
    print(f"\n📋 Summary: {result.short_summary}")
    
    print(f"\n🔍 Follow-up questions:")
    for i, question in enumerate(result.follow_up_questions, 1):
        print(f"   {i}. {question}")
    
    print(f"\n📄 Research Result:")
    print("=" * 60)
    print(result.markdown_report)


if __name__ == "__main__":
    asyncio.run(main())
