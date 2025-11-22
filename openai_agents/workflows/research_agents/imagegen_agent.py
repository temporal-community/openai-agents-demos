from datetime import timedelta

from agents import Agent
from pydantic import BaseModel
from temporalio.contrib import openai_agents as temporal_agents

from openai_agents.workflows.image_generation_activity import generate_image

IMAGE_GEN_PROMPT = (
    "You are an expert visual content specialist who creates compelling images "
    "for research reports. You will be provided with a research query that has been enriched "
    "with user preferences and context.\\n\\n"
    "Your responsibilities:\\n"
    "1. Analyze the research topic and identify key visual themes\\n"
    "2. Generate a 2-sentence image description that captures the essence of the research\\n"
    "3. Call the generate_image tool with your description to create the actual image\\n"
    "4. Return the results with the image file path and notes about the visual concept\\n\\n"
    "Guidelines for image descriptions:\\n"
    "- Focus on professional, illustrative imagery that enhances understanding\\n"
    "- Avoid text-heavy images or screenshots\\n"
    "- Prefer abstract concepts, diagrams, or representative scenes\\n"
    "- Consider the research domain (business, science, technology, etc.)\\n"
    "- Make descriptions specific and detailed for high-quality output\\n\\n"
    "Examples:\\n"
    "- Research query: 'Sustainable energy solutions for small businesses'\\n"
    "  Image description: 'A modern small business building with solar panels on the roof "
    "and a wind turbine in the background, depicted in a clean, professional illustration style. "
    "The scene shows integration of renewable energy in an urban commercial setting.'\\n\\n"
    "- Research query: 'Impact of artificial intelligence on healthcare diagnostics'\\n"
    "  Image description: 'A futuristic medical setting showing a doctor using an AI-powered "
    "diagnostic interface with holographic displays of medical scans and data visualizations. "
    "The image conveys advanced technology seamlessly integrated into patient care.'\\n\\n"
    "IMPORTANT: After calling generate_image tool:\\n"
    "- Set success to true if the tool returns success=true\\n"
    "- Include the image_file_path from the tool response in your output\\n"
    "- If the tool fails, set success to false and include the error message"
)


class ImageGenData(BaseModel):
    """Output from image generation agent"""

    success: bool
    """Whether image generation was successful"""

    image_description: str
    """The 2-sentence description used for generating the image"""

    image_file_path: str | None = None
    """Path to the generated image file (if successful)"""

    notes: str
    """Notes about the visual concept and design choices"""

    error_message: str | None = None
    """Error message if image generation failed"""


def new_imagegen_agent() -> Agent:
    """Create a new image generation agent."""
    return Agent(
        name="ImageGenAgent",
        instructions=IMAGE_GEN_PROMPT,
        model="gpt-4o-mini",  # Fast, cost-effective for description generation
        tools=[
            temporal_agents.workflow.activity_as_tool(
                generate_image, start_to_close_timeout=timedelta(seconds=60)
            )
        ],
        output_type=ImageGenData,
    )
