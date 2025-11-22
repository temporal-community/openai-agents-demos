from dataclasses import dataclass
from typing import Any

from temporalio import workflow

from openai_agents.workflows.research_agents.research_manager import (
    InteractiveResearchManager,
)
from openai_agents.workflows.research_agents.research_models import (
    ClarificationInput,
    ResearchInteractionDict,
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
        # Simple instance variables instead of complex dataclass
        self.original_query: str | None = None
        self.clarification_questions: list[str] = []
        self.clarification_responses: dict[str, str] = {}
        self.current_question_index: int = 0
        self.report_data: Any | None = None
        self.research_completed: bool = False
        self.workflow_ended: bool = False
        self.research_initialized: bool = False

    def _build_result(
        self,
        summary: str,
        report: str,
        questions: list[str] | None = None,
        pdf_path: str | None = None,
    ) -> InteractiveResearchResult:
        """Helper to build InteractiveResearchResult"""
        return InteractiveResearchResult(
            short_summary=summary,
            markdown_report=report,
            follow_up_questions=questions or [],
            pdf_file_path=pdf_path,
        )

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
            pdf_file_path = await self.research_manager._generate_pdf_report(
                report_data
            )
            return self._build_result(
                report_data.short_summary,
                report_data.markdown_report,
                report_data.follow_up_questions,
                pdf_file_path,
            )

        # Main workflow loop - wait for research to be started and completed
        while True:
            workflow.logger.info("Waiting for research to start or complete...")

            # Wait for workflow end signal, research completion, or research initialization
            await workflow.wait_condition(
                lambda: self.workflow_ended
                or self.research_completed
                or self.research_initialized
            )

            # If workflow was signaled to end, exit gracefully
            if self.workflow_ended:
                return self._build_result(
                    "Research ended by user", "Research workflow ended by user"
                )

            # If research has been completed, return results
            if self.research_completed and self.report_data:
                # Generate PDF if we have report data
                pdf_file_path = await self.research_manager._generate_pdf_report(
                    self.report_data
                )
                return self._build_result(
                    self.report_data.short_summary,
                    self.report_data.markdown_report,
                    self.report_data.follow_up_questions,
                    pdf_file_path,
                )

            # If research is initialized but not completed, handle the clarification flow
            if self.research_initialized and not self.research_completed:

                # If we have clarification questions, wait for all responses
                if self.clarification_questions:
                    # Wait for all clarifications to be collected
                    await workflow.wait_condition(
                        lambda: self.workflow_ended
                        or len(self.clarification_responses)
                        >= len(self.clarification_questions)
                    )

                    if self.workflow_ended:
                        return self._build_result(
                            "Research ended by user", "Research workflow ended by user"
                        )

                    # Complete research with clarifications
                    if self.original_query:  # Type guard to ensure it's not None
                        self.report_data = await self.research_manager.run_with_clarifications_complete(
                            self.original_query,
                            self.clarification_questions,
                            self.clarification_responses,
                        )

                    self.research_completed = True
                    continue

                # If we already have report data (from direct research), mark as completed
                elif self.report_data is not None:
                    self.research_completed = True
                    continue

                # If no clarification questions and no report data, it means research failed
                return self._build_result(
                    "No research completed", "Research failed to start properly"
                )

    def _get_current_question(self) -> str | None:
        """Get the current question that needs an answer"""
        if self.current_question_index >= len(self.clarification_questions):
            return None
        return self.clarification_questions[self.current_question_index]

    def _has_more_questions(self) -> bool:
        """Check if there are more questions to answer"""
        return self.current_question_index < len(self.clarification_questions)

    @workflow.query
    def get_status(self) -> ResearchInteractionDict:
        """Get current research status"""
        current_question = self._get_current_question()

        # Determine status based on workflow state
        if self.workflow_ended:
            status = "ended"
        elif self.research_completed:
            status = "completed"
        elif self.clarification_questions and len(self.clarification_responses) < len(
            self.clarification_questions
        ):
            if len(self.clarification_responses) == 0:
                status = "awaiting_clarifications"
            else:
                status = "collecting_answers"
        elif self.original_query and not self.research_completed:
            status = "researching"
        else:
            status = "pending"

        return ResearchInteractionDict(
            original_query=self.original_query,
            clarification_questions=self.clarification_questions,
            clarification_responses=self.clarification_responses,
            current_question_index=self.current_question_index,
            current_question=current_question,
            status=status,
            research_completed=self.research_completed,
        )

    @workflow.update
    async def start_research(self, input: UserQueryInput) -> ResearchInteractionDict:
        """Start a new research session with clarifying questions flow"""
        workflow.logger.info(f"Starting research for query: '{input.query}'")
        self.original_query = input.query

        # Immediately check if clarifications are needed
        result = await self.research_manager.run_with_clarifications_start(
            self.original_query
        )

        if result.needs_clarifications:
            # Set up clarifying questions for client to see immediately
            self.clarification_questions = result.questions or []
        else:
            # No clarifications needed, store the research data but let main loop complete it
            if result.report_data is not None:
                self.report_data = result.report_data
            # If research failed, main loop will handle fallback

        # Mark research as initialized so main loop can proceed
        self.research_initialized = True

        return self.get_status()

    @workflow.update
    async def provide_single_clarification(
        self, input: SingleClarificationInput
    ) -> ResearchInteractionDict:
        """Provide a single clarification response"""
        current_question = self._get_current_question()
        workflow.logger.info(
            f"Received clarification answer {self.current_question_index + 1}/{len(self.clarification_questions)}: '{input.answer}' for question: '{current_question}'"
        )

        # Store answer with question index format for compatibility
        question_key = f"question_{self.current_question_index}"
        self.clarification_responses[question_key] = input.answer
        self.current_question_index += 1

        return self.get_status()

    @workflow.update
    async def provide_clarifications(
        self, input: ClarificationInput
    ) -> ResearchInteractionDict:
        """Provide all clarification responses at once (legacy compatibility)"""
        workflow.logger.info(
            f"Received {len(input.responses)} clarification responses: {input.responses}"
        )

        self.clarification_responses = input.responses
        # Mark all questions as answered
        self.current_question_index = len(self.clarification_questions)

        return self.get_status()

    @provide_single_clarification.validator
    def validate_single_clarification(self, input: SingleClarificationInput) -> None:
        if not input.answer.strip():
            raise ValueError("Answer cannot be empty")

        if not self.original_query:
            raise ValueError("No active research interaction")

        if not self.clarification_questions or len(self.clarification_responses) >= len(
            self.clarification_questions
        ):
            raise ValueError("Not collecting clarifications")

    @provide_clarifications.validator
    def validate_provide_clarifications(self, input: ClarificationInput) -> None:
        if not input.responses:
            raise ValueError("Clarification responses cannot be empty")

        if not self.original_query:
            raise ValueError("No active research interaction")

        if not self.clarification_questions:
            raise ValueError("Not awaiting clarifications")

    @workflow.signal
    async def end_workflow_signal(self) -> None:
        """Signal to end the workflow"""
        self.workflow_ended = True
