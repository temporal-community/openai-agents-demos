from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    # TODO: Restore progress updates
    from agents import (
        RunConfig,
        Runner,
        TResponseInputItem,
        custom_span,
        gen_trace_id,
        trace,
    )

    from openai_agents.workflows.research_agents.clarifying_agent import Clarifications
    from openai_agents.workflows.research_agents.imagegen_agent import (
        ImageGenData,
        new_imagegen_agent,
    )
    from openai_agents.workflows.research_agents.pdf_generator_agent import (
        new_pdf_generator_agent,
    )

    # from openai_agents.workflows.research_agents.instruction_agent import (
    #     new_instruction_agent,
    # )
    from openai_agents.workflows.research_agents.planner_agent import (
        WebSearchItem,
        WebSearchPlan,
        new_planner_agent,
    )
    from openai_agents.workflows.research_agents.search_agent import new_search_agent
    from openai_agents.workflows.research_agents.triage_agent import new_triage_agent
    from openai_agents.workflows.research_agents.writer_agent import (
        ReportData,
        new_writer_agent,
    )

    from openai_agents.workflows.image_generation_activity import (
        ImageStylingOptions,
        generate_image,
    )
    from openai_agents.workflows.pdf_generation_activity import ImageData


@dataclass
class ClarificationResult:
    """Result from initial clarification check"""

    needs_clarifications: bool
    questions: Optional[List[str]] = None
    research_output: Optional[str] = None
    report_data: Optional[ReportData] = None


class InteractiveResearchManager:
    def __init__(self):
        self.run_config = RunConfig()
        self.search_agent = new_search_agent()
        self.planner_agent = new_planner_agent()
        self.writer_agent = new_writer_agent()
        self.triage_agent = new_triage_agent()
        self.pdf_generator_agent = new_pdf_generator_agent()
        self.imagegen_agent = new_imagegen_agent()

        # Image state (stored during generation for PDF embedding)
        self.research_image_path: str | None = None
        self.research_image_description: str | None = None

    async def run(self, query: str, use_clarifications: bool = False) -> str:
        """
        Run research with optional clarifying questions flow

        Args:
            query: The research query
            use_clarifications: If True, uses multi-agent flow with clarifying questions
        """
        if use_clarifications:
            # This method is for backwards compatibility, just use direct flow
            report = await self._run_direct(query)
            return report.markdown_report
        else:
            report = await self._run_direct(query)
            return report.markdown_report

    async def _run_direct(self, query: str) -> ReportData:
        """Original direct research flow with parallel image generation"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            # Start image generation immediately to run in parallel with entire research pipeline
            workflow.logger.info(
                "Starting image generation in parallel with research pipeline"
            )
            image_task = asyncio.create_task(self._generate_research_image(query))

            # Perform research pipeline (planning, searching, writing)
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(query, search_results)

            # Wait for image generation to complete (if not already done)
            workflow.logger.info("Waiting for image generation to complete")
            image_path, image_description = await image_task

            # Store image data for PDF generation
            self.research_image_path = image_path
            self.research_image_description = image_description

        return report

    async def run_with_clarifications_start(self, query: str) -> ClarificationResult:
        """Start clarification flow and return whether clarifications are needed"""
        trace_id = gen_trace_id()
        with trace("Clarification check", trace_id=trace_id):
            # Start with triage agent to determine if clarifications are needed
            input_items: list[TResponseInputItem] = [{"content": query, "role": "user"}]
            result = await Runner.run(
                self.triage_agent,
                input_items,
                run_config=self.run_config,
            )

            # Check if clarifications were generated
            clarifications = self._extract_clarifications(result)
            if clarifications and isinstance(clarifications, Clarifications):
                return ClarificationResult(
                    needs_clarifications=True, questions=clarifications.questions
                )
            else:
                # No clarifications needed, continue with research
                # Start image generation immediately to run in parallel with entire research pipeline
                workflow.logger.info(
                    "Starting image generation in parallel with research pipeline"
                )
                image_task = asyncio.create_task(self._generate_research_image(query))

                # Perform research pipeline (planning, searching, writing)
                search_plan = await self._plan_searches(query)
                search_results = await self._perform_searches(search_plan)
                report = await self._write_report(query, search_results)

                # Wait for image generation to complete (if not already done)
                workflow.logger.info("Waiting for image generation to complete")
                image_path, image_description = await image_task

                # Store image data for PDF generation
                self.research_image_path = image_path
                self.research_image_description = image_description

                return ClarificationResult(
                    needs_clarifications=False,
                    research_output=report.markdown_report,
                    report_data=report,
                )

    async def run_with_clarifications_complete(
        self, original_query: str, questions: List[str], responses: Dict[str, str]
    ) -> ReportData:
        """Complete research using clarification responses"""
        trace_id = gen_trace_id()
        with trace("Enhanced Research with clarifications", trace_id=trace_id):
            # Enrich the query with clarification responses
            enriched_query = self._enrich_query(original_query, questions, responses)

            # Start image generation immediately to run in parallel with entire research pipeline
            workflow.logger.info(
                "Starting image generation in parallel with research pipeline"
            )
            image_task = asyncio.create_task(self._generate_research_image(enriched_query))

            # Perform research pipeline (planning, searching, writing)
            search_plan = await self._plan_searches(enriched_query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(enriched_query, search_results)

            # Wait for image generation to complete (if not already done)
            workflow.logger.info("Waiting for image generation to complete")
            image_path, image_description = await image_task

            # Store image data for PDF generation
            self.research_image_path = image_path
            self.research_image_description = image_description

            return report

    def _extract_clarifications(self, result) -> Optional[Clarifications]:
        """Extract clarifications from agent result if present"""
        try:
            # Check if the final output is Clarifications
            if hasattr(result, "final_output") and isinstance(
                result.final_output, Clarifications
            ):
                return result.final_output

            # Look through result items for clarifications
            for item in result.new_items:
                if hasattr(item, "raw_item") and hasattr(item.raw_item, "content"):
                    content = item.raw_item.content
                    if isinstance(content, Clarifications):
                        return content
                # Also check if the item itself has output_type content
                if hasattr(item, "output") and isinstance(item.output, Clarifications):
                    return item.output

            # Try result.final_output_as() method if available
            try:
                clarifications = result.final_output_as(Clarifications)
                if clarifications:
                    return clarifications
            except Exception:
                pass

            return None
        except Exception as e:
            workflow.logger.info(f"Error extracting clarifications: {e}")
            return None

    def _enrich_query(
        self, original_query: str, questions: List[str], responses: Dict[str, str]
    ) -> str:
        """Combine original query with clarification responses"""
        enriched = f"Original query: {original_query}\n\nAdditional context from clarifications:\n"
        for i, question in enumerate(questions):
            answer = responses.get(f"question_{i}", "No specific preference")
            enriched += f"- {question}: {answer}\n"
        return enriched

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        input_str: str = f"Query: {query}"
        result = await Runner.run(
            self.planner_agent,
            input_str,
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
        input_str: str = (
            f"Search term: {item.query}\nReason for searching: {item.reason}"
        )
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
        input_str: str = (
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

    async def _generate_research_image(self, query: str) -> tuple[str | None, str | None]:
        """
        Generate an image for the research topic.

        Steps:
        1. Use ImageGenAgent to create a compelling 2-sentence description
        2. Call image generation activity which generates and saves the image to temp file
        3. Return temp file path and description

        Args:
            query: The enriched research query

        Returns:
            Tuple of (image_file_path, description) or (None, None) if failed
        """
        with custom_span("Generate research image"):
            try:
                # Step 1: Generate image description using the agent (no tool)
                workflow.logger.info("Creating image description...")

                result = await Runner.run(
                    self.imagegen_agent,
                    f"Create a 2-sentence image description for: {query}",
                    run_config=self.run_config,
                )

                image_output = result.final_output_as(ImageGenData)

                if not image_output.success:
                    workflow.logger.warning("Failed to create image description")
                    return (None, None)

                # Step 2: Call image generation activity directly
                workflow.logger.info(
                    f"Generating image with description: {image_output.image_description}"
                )

                try:
                    image_result = await workflow.execute_activity(
                        generate_image,
                        args=[image_output.image_description, ImageStylingOptions()],
                        start_to_close_timeout=timedelta(seconds=60),
                    )

                    if not image_result.success or not image_result.image_file_path:
                        workflow.logger.warning(
                            f"Image generation failed: {image_result.error_message}"
                        )
                        return (None, None)
                except Exception as e:
                    # Handle non-retryable errors (e.g., organization not verified, serialization errors)
                    workflow.logger.warning(
                        f"Image generation activity failed: {str(e)}. Continuing without image."
                    )
                    return (None, None)

                workflow.logger.info(
                    f"Image generated successfully, saved to: {image_result.image_file_path}"
                )

                # Return file path directly (no need to save again)
                return (
                    image_result.image_file_path,
                    image_output.image_description,
                )

            except Exception as e:
                workflow.logger.error(f"Error generating research image: {str(e)}")
                return (None, None)

    async def _generate_pdf_report(self, report_data: ReportData) -> str | None:
        """Generate PDF from markdown report using PDF generator agent"""
        with custom_span("Generate PDF report"):
            try:
                workflow.logger.info("Generating PDF report with PDF generator agent...")

                # Build prompt for PDF generator with image path if available
                if self.research_image_path:
                    prompt = f"""Convert this markdown report to PDF and include the specified hero image.

IMAGE_PATH: {self.research_image_path}

MARKDOWN CONTENT:
{report_data.markdown_report}

Instructions: Use the image at IMAGE_PATH as the hero image parameter when calling the generate_pdf tool. The image should appear under the document title."""
                else:
                    prompt = f"Convert this markdown report to PDF:\n\n{report_data.markdown_report}"

                # Call PDF generator agent
                pdf_result = await Runner.run(
                    self.pdf_generator_agent,
                    prompt,
                    run_config=self.run_config,
                )

                from openai_agents.workflows.research_agents.pdf_generator_agent import PDFReportData
                pdf_output = pdf_result.final_output_as(PDFReportData)

                if pdf_output.success and pdf_output.pdf_file_path:
                    workflow.logger.info(
                        f"PDF generated successfully: {pdf_output.pdf_file_path}"
                    )

                    # Cleanup temp image file if it exists
                    await self._cleanup_temp_image()

                    return pdf_output.pdf_file_path
                else:
                    workflow.logger.warning(
                        f"PDF generation failed: {pdf_output.error_message}"
                    )
                    # Still cleanup even on failure
                    await self._cleanup_temp_image()
                    return None

            except Exception as e:
                workflow.logger.error(f"Error generating PDF: {str(e)}")
                # Cleanup on exception
                await self._cleanup_temp_image()
                return None

    async def _cleanup_temp_image(self) -> None:
        """Clean up temporary image file"""
        if self.research_image_path:
            try:
                from pathlib import Path
                image_file = Path(self.research_image_path)
                if image_file.exists():
                    image_file.unlink()
                    workflow.logger.info(f"Cleaned up temp image: {self.research_image_path}")
            except Exception as e:
                workflow.logger.warning(f"Failed to cleanup temp image: {str(e)}")
            finally:
                self.research_image_path = None
