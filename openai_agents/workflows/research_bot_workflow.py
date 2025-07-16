from temporalio import workflow

from openai_agents.workflows.simple_research_manager import SimpleResearchManager


@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, query: str) -> str:
        return await SimpleResearchManager().run(query)
