from temporalio import workflow

from openai_agents.workflows.research_agents.research_manager import ResearchManager
from openai_agents.workflows.research_agents.research_models import (
    ClarificationInput,
    ResearchInteraction,
    ResearchStatusInput,
    SingleClarificationInput,
    UserQueryInput,
)


@workflow.defn
class InteractiveResearchWorkflow:
    def __init__(self):
        self.research_manager = ResearchManager()
        self.current_interaction: ResearchInteraction | None = None
        self._end_workflow = False

    @workflow.run
    async def run(
        self, initial_query: str | None = None, use_clarifications: bool = False
    ) -> str:
        """
        Run research workflow - long-running interactive workflow following wealth management pattern

        Args:
            initial_query: Optional initial research query (for backward compatibility)
            use_clarifications: If True, enables interactive clarifying questions (for backward compatibility)
        """
        if initial_query and not use_clarifications:
            # Simple direct research mode - backward compatibility
            return await self.research_manager.run(
                initial_query, use_clarifications=False
            )

        # Long-running workflow - wait for termination or completion like wealth management
        await workflow.wait_condition(
            lambda: bool(
                self._end_workflow
                or (
                    self.current_interaction
                    and self.current_interaction.status == "completed"
                )
            )
        )

        if self._end_workflow:
            return "Research workflow ended by user"

        return (
            self.current_interaction.final_result or "No research completed"
            if self.current_interaction
            else "No research completed"
        )

    async def _start_interactive_research(self, query: str):
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
            # No clarifications needed, proceed directly to research
            self.current_interaction.final_result = result.research_output
            self.current_interaction.status = "completed"

    async def _complete_research_with_clarifications(self):
        """Complete research using collected clarifications"""
        if (
            not self.current_interaction
            or not self.current_interaction.clarification_responses
        ):
            return

        self.current_interaction.status = "researching"

        questions = self.current_interaction.clarification_questions or []
        responses = self.current_interaction.clarification_responses or {}

        # Continue with research using clarifications
        final_result = await self.research_manager.run_with_clarifications_complete(
            self.current_interaction.original_query, questions, responses
        )

        self.current_interaction.final_result = final_result
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
            # All questions answered, proceed with research
            await self._complete_research_with_clarifications()

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

        # Proceed with research
        await self._complete_research_with_clarifications()

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
    async def end_workflow_signal(self):
        """Signal to end the workflow"""
        self._end_workflow = True
