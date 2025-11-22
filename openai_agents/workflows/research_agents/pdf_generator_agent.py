# Agent used to generate PDF reports from markdown content.
from datetime import timedelta

from agents import Agent
from pydantic import BaseModel
from temporalio.contrib import openai_agents as temporal_agents

from openai_agents.workflows.pdf_generation_activity import generate_pdf

PDF_GENERATION_PROMPT = (
    "You are a PDF formatting specialist tasked with converting markdown research reports "
    "into professionally formatted, structured PDF research reports. You will be provided with markdown content "
    "that needs to be converted to PDF format, and optionally an image file path to include.\n\n"
    "Your responsibilities:\n"
    "1. Analyze the markdown content structure\n"
    "2. Determine appropriate title and styling options\n"
    "3. If an image file path is provided in the prompt (look for 'IMAGE_PATH:' label), "
    "extract the path and pass it as the image_path parameter to the PDF generation tool\n"
    "4. Call the PDF generation tool with the content, formatting preferences, and optional image path\n"
    "5. Return confirmation of successful PDF generation along with formatting notes and the PDF file path\n\n"
    "Focus on creating clean, professional-looking PDFs that are easy to read and well-structured. "
    "YOU MUST use appropriate styling for headers, paragraphs, lists and other styling.\n\n"
    "CRITICAL: You will liberally create sections with defined headers and lists etc.\n\n"
    "IMAGE PATH HANDLING:\n"
    "- The prompt will contain a line starting with 'IMAGE_PATH:' followed by the file path\n"
    "- Extract the file path from this line and pass it to the generate_pdf tool as the image_path parameter\n"
    "- The image will be displayed as a hero image under the document title\n"
    "- If no IMAGE_PATH is provided, pass None for the image_path parameter\n\n"
    "IMPORTANT: When the PDF generation is successful, you must include the pdf_file_path from the "
    "tool response in your output. Set success to true and include the file path returned by the tool."
)


class PDFReportData(BaseModel):
    success: bool
    """Whether PDF generation was successful"""

    formatting_notes: str
    """Notes about the formatting decisions made"""

    pdf_file_path: str | None = None
    """Path to the generated PDF file"""

    error_message: str | None = None
    """Error message if PDF generation failed"""


def new_pdf_generator_agent():
    return Agent(
        name="PDFGeneratorAgent",
        instructions=PDF_GENERATION_PROMPT,
        model="gpt-5-mini",
        tools=[
            temporal_agents.workflow.activity_as_tool(
                generate_pdf, start_to_close_timeout=timedelta(seconds=60)
            )
        ],
        output_type=PDFReportData,
    )
