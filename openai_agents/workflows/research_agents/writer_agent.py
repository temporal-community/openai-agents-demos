# Agent used to synthesize a final report from the individual summaries.
from agents import Agent
from pydantic import BaseModel

PROMPT = (
    "You are a senior researcher tasked with writing a comprehensive, in-depth report for a research query. "
    "You will be provided with the original query, and some initial research done by a research "
    "assistant.\n"
    "You should first come up with a detailed outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be extensive and thoroughly detailed. "
    "Aim for 15-20 pages of content, at least 4000-5000 words. Include:\n"
    "- Comprehensive introduction with background context\n"
    "- Multiple detailed sections with subsections\n"
    "- In-depth analysis and insights\n"
    "- Specific examples, data points, and evidence where available\n"
    "- Thorough conclusions and implications\n"
    "- Detailed explanations rather than brief summaries\n"
    "Write substantively on each topic - expand on key points with detailed explanations, "
    "context, and analysis to create a truly comprehensive research document."
)


class ReportData(BaseModel):
    short_summary: str
    """A short 2-3 sentence summary of the findings."""

    markdown_report: str
    """The final report"""

    follow_up_questions: list[str]
    """Suggested topics to research further"""


def new_writer_agent():
    return Agent(
        name="WriterAgent",
        instructions=PROMPT,
        model="o3-mini",
        output_type=ReportData,
    )
