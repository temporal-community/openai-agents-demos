from temporalio import workflow
from dataclasses import dataclass

from openai_agents.workflows.simple_research_manager import SimpleResearchManager


@dataclass
class ResearchWorkflowResult:
    """Result from research workflow including both markdown and PDF"""
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]
    pdf_file_path: str | None = None


@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, query: str) -> ResearchWorkflowResult:
        manager = SimpleResearchManager()
        # Get the full report data
        search_plan = await manager._plan_searches(query)
        search_results = await manager._perform_searches(search_plan)
        report_data = await manager._write_report(query, search_results)
        
        # Generate PDF separately
        pdf_file_path = await manager._generate_pdf_report(report_data)
        
        return ResearchWorkflowResult(
            short_summary=report_data.short_summary,
            markdown_report=report_data.markdown_report,
            follow_up_questions=report_data.follow_up_questions,
            pdf_file_path=pdf_file_path
        )
