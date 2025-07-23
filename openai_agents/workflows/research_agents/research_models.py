from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ClarificationInput(BaseModel):
    """Input for providing clarification responses"""

    responses: Dict[str, str]  # question -> answer mapping


class SingleClarificationInput(BaseModel):
    """Input for providing a single clarification response"""

    question_index: int
    answer: str


class UserQueryInput(BaseModel):
    """Input for initial user research query"""

    query: str


class ResearchStatusInput(BaseModel):
    """Input for getting research status"""

    pass


@dataclass
class ResearchInteraction:
    """Represents a research interaction with clarifications"""

    original_query: str
    clarification_questions: Optional[List[str]] = None
    clarification_responses: Optional[Dict[str, str]] = None
    current_question_index: int = 0
    enriched_query: Optional[str] = None
    final_result: Optional[str] = None
    report_data: Optional[Any] = None  # Will hold ReportData object
    status: str = "pending"  # pending, awaiting_clarifications, collecting_answers, researching, completed

    def get_current_question(self) -> Optional[str]:
        """Get the current question that needs an answer"""
        if not self.clarification_questions or self.current_question_index >= len(
            self.clarification_questions
        ):
            return None
        return self.clarification_questions[self.current_question_index]

    def has_more_questions(self) -> bool:
        """Check if there are more questions to answer"""
        if not self.clarification_questions:
            return False
        return self.current_question_index < len(self.clarification_questions)

    def answer_current_question(self, answer: str) -> bool:
        """Answer the current question and advance. Returns True if more questions remain."""
        if not self.clarification_questions:
            return False

        if self.clarification_responses is None:
            self.clarification_responses = {}

        # Store answer with question_index format for compatibility
        question_key = f"question_{self.current_question_index}"
        self.clarification_responses[question_key] = answer

        self.current_question_index += 1
        return self.has_more_questions()

    def __str__(self):
        questions_progress = (
            f"{self.current_question_index}/{len(self.clarification_questions or [])}"
        )
        return f"Query: {self.original_query}, Status: {self.status}, Questions: {questions_progress}"


class ResearchInteractionDict(BaseModel):
    """Compatibility wrapper that provides ResearchInteraction-like interface"""

    original_query: str | None = None
    clarification_questions: list[str] = []
    clarification_responses: dict[str, str] = {}
    current_question_index: int = 0
    current_question: str | None = None
    status: str = "pending"
    research_completed: bool = False
    final_result: str | None = None

    def get_current_question(self) -> str | None:
        """Get the current question that needs an answer"""
        return self.current_question

    def has_more_questions(self) -> bool:
        """Check if there are more questions to answer"""
        return self.current_question_index < len(self.clarification_questions)
