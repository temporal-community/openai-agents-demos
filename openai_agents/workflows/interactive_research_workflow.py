from temporalio import workflow
from dataclasses import dataclass

from openai_agents.workflows.research_agents.research_manager import (
    InteractiveResearchManager,
)
from openai_agents.workflows.research_agents.research_models import (
    ClarificationInput,
    ResearchInteraction,
    SingleClarificationInput,
    UserQueryInput,
)


@dataclass
class InteractiveResearchResult:
    """Result from interactive research workflow including both markdown and PDF"""
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]
    pdf_file_path: str | None = None


@workflow.defn
class InteractiveResearchWorkflow:
    def __init__(self) -> None:
        self.research_manager = InteractiveResearchManager()
        self.current_interaction: ResearchInteraction | None = None
        self._end_workflow = False

    @workflow.run
    async def run(
        self, initial_query: str | None = None, use_clarifications: bool = False
    ) -> InteractiveResearchResult:
        """
        Run research workflow - long-running interactive workflow with clarifying questions

        Args:
            initial_query: Optional initial research query (for backward compatibility)
            use_clarifications: If True, enables interactive clarifying questions (for backward compatibility)
        """
        if initial_query and not use_clarifications:
            # Simple direct research mode - backward compatibility
            report_data = await self.research_manager._run_direct(initial_query)
            pdf_file_path = await self.research_manager._generate_pdf_report(report_data)
            return InteractiveResearchResult(
                short_summary=report_data.short_summary,
                markdown_report=report_data.markdown_report,
                follow_up_questions=report_data.follow_up_questions,
                pdf_file_path=pdf_file_path
            )

        # Wait for user to start the research via an update and for clarifications to be collected.
        # The workflow will pause here until the status is 'researching' or 'completed'.
        await workflow.wait_condition(
            lambda: self._end_workflow
            or (
                self.current_interaction is not None
                and self.current_interaction.status in ["researching", "completed"]
            )
        )

        # If the workflow was signaled to end, exit gracefully.
        if self._end_workflow:
            return InteractiveResearchResult(
                short_summary="Research ended by user",
                markdown_report="Research workflow ended by user",
                follow_up_questions=[],
                pdf_file_path=None
            )

        # If we are now in the 'researching' state, perform the long-running work.
        if (
            self.current_interaction
            and self.current_interaction.status == "researching"
        ):
            await self._complete_research_with_clarifications()

        # At this point, the workflow is complete, so we return the final result.
        if self.current_interaction and self.current_interaction.report_data:
            # Generate PDF if we have report data
            pdf_file_path = await self.research_manager._generate_pdf_report(self.current_interaction.report_data)
            return InteractiveResearchResult(
                short_summary=self.current_interaction.report_data.short_summary,
                markdown_report=self.current_interaction.report_data.markdown_report,
                follow_up_questions=self.current_interaction.report_data.follow_up_questions,
                pdf_file_path=pdf_file_path
            )
        else:
            final_result = "No research completed"
            if self.current_interaction and self.current_interaction.final_result:
                final_result = self.current_interaction.final_result
            return InteractiveResearchResult(
                short_summary="No research completed",
                markdown_report=final_result,
                follow_up_questions=[],
                pdf_file_path=None
            )

    async def _start_interactive_research(self, query: str) -> None:
        """Start interactive research with clarifying questions"""
        self.current_interaction = ResearchInteraction(
            original_query=query, status="pending"
        )

        # Start the clarification flow
        result = await self.research_manager.run_with_clarifications_start(query)

        if result.needs_clarifications:
            self.current_interaction.clarification_questions = result.questions
            self.current_interaction.status = "awaiting_clarifications"
        else:
            # No clarifications needed, set status to researching first
            self.current_interaction.status = "researching"
            # Give UI time to show the researching status
            await workflow.sleep(0.1)
            # The research result should already be complete from the manager
            self.current_interaction.final_result = result.research_output
            self.current_interaction.report_data = result.report_data
            self.current_interaction.status = "completed"

    async def _complete_research_with_clarifications(self) -> None:
        """Complete research using collected clarifications"""
        if (
            not self.current_interaction
            or not self.current_interaction.clarification_responses
        ):
            return

        # NOTE: The status is already 'researching'. This method now only does the work.
        questions = self.current_interaction.clarification_questions or []
        responses = self.current_interaction.clarification_responses or {}

        # Continue with research using clarifications
        report_data = await self.research_manager.run_with_clarifications_complete(
            self.current_interaction.original_query, questions, responses
        )

        self.current_interaction.final_result = report_data.markdown_report
        self.current_interaction.report_data = report_data
        self.current_interaction.status = "completed"

    @workflow.query
    def get_status(self) -> ResearchInteraction | None:
        """Get current research status"""
        return self.current_interaction

    @workflow.update
    async def start_research(self, input: UserQueryInput) -> ResearchInteraction:
        """Start a new research session with clarifying questions flow"""
        # Always use clarifying questions for interactive mode
        await self._start_interactive_research(input.query)
        if not self.current_interaction:
            raise RuntimeError("Failed to start research interaction")
        return self.current_interaction

    @workflow.update
    async def provide_single_clarification(
        self, input: SingleClarificationInput
    ) -> ResearchInteraction:
        """Provide a single clarification response"""
        if not self.current_interaction:
            raise ValueError("No active research interaction")

        if self.current_interaction.status not in [
            "awaiting_clarifications",
            "collecting_answers",
        ]:
            raise ValueError(
                f"Not collecting clarifications. Current status: {self.current_interaction.status}"
            )

        # Update status to collecting answers if this is the first answer
        if self.current_interaction.status == "awaiting_clarifications":
            self.current_interaction.status = "collecting_answers"

        # Answer the current question and check if more remain
        has_more = self.current_interaction.answer_current_question(input.answer)

        if not has_more:
            # All questions answered. Set status to 'researching' and return immediately.
            # The main run() method will detect this change and execute the research.
            self.current_interaction.status = "researching"

        return self.current_interaction

    @workflow.update
    async def provide_clarifications(
        self, input: ClarificationInput
    ) -> ResearchInteraction:
        """Provide all clarification responses at once (legacy compatibility)"""
        if not self.current_interaction:
            raise ValueError("No active research interaction")

        if self.current_interaction.status != "awaiting_clarifications":
            raise ValueError(
                f"Not awaiting clarifications. Current status: {self.current_interaction.status}"
            )

        self.current_interaction.clarification_responses = input.responses
        # Mark all questions as answered
        self.current_interaction.current_question_index = len(
            self.current_interaction.clarification_questions or []
        )

        # Set status to researching and let the run method handle it
        self.current_interaction.status = "researching"

        return self.current_interaction

    @provide_single_clarification.validator
    def validate_single_clarification(self, input: SingleClarificationInput) -> None:
        if not input.answer.strip():
            raise ValueError("Answer cannot be empty")

    @provide_clarifications.validator
    def validate_provide_clarifications(self, input: ClarificationInput) -> None:
        if not input.responses:
            raise ValueError("Clarification responses cannot be empty")

    @workflow.signal
    async def end_workflow_signal(self) -> None:
        """Signal to end the workflow"""
        self._end_workflow = True
