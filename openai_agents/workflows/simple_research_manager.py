from __future__ import annotations

import asyncio

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import RunConfig, Runner, custom_span, gen_trace_id, trace

    from openai_agents.workflows.research_agents.planner_agent import (
        WebSearchItem,
        WebSearchPlan,
        new_planner_agent,
    )
    from openai_agents.workflows.research_agents.search_agent import new_search_agent
    from openai_agents.workflows.research_agents.writer_agent import (
        ReportData,
        new_writer_agent,
    )


class SimpleResearchManager:
    def __init__(self):
        self.run_config = RunConfig()
        self.search_agent = new_search_agent()
        self.planner_agent = new_planner_agent()
        self.writer_agent = new_writer_agent()

    async def run(self, query: str) -> str:
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(query, search_results)

        return report.markdown_report

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(
            self.planner_agent,
            f"Query: {query}",
            run_config=self.run_config,
        )
        return result.final_output_as(WebSearchPlan)

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        with custom_span("Search the web"):
            num_completed = 0
            tasks = [
                asyncio.create_task(self._search(item)) for item in search_plan.searches
            ]
            results = []
            for task in workflow.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
            return results

    async def _search(self, item: WebSearchItem) -> str | None:
        input_str = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                self.search_agent,
                input_str,
                run_config=self.run_config,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        input_str = (
            f"Original query: {query}\nSummarized search results: {search_results}"
        )

        # Generate markdown report
        markdown_result = await Runner.run(
            self.writer_agent,
            input_str,
            run_config=self.run_config,
        )

        report_data = markdown_result.final_output_as(ReportData)
        return report_data
