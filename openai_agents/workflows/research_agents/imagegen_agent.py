from agents import Agent
from pydantic import BaseModel


IMAGE_GEN_PROMPT = (
    "You are an expert visual content specialist who creates compelling image descriptions "
    "for research reports. You will be provided with a research query that has been enriched "
    "with user preferences and context.\\n\\n"
    "Your responsibilities:\\n"
    "1. Analyze the research topic and identify key visual themes\\n"
    "2. Generate a 2-sentence image description that captures the essence of the research\\n"
    "3. Return your description with notes about the visual concept\\n\\n"
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
    "IMPORTANT: You must set success to true when you successfully create an image description, "
    "and include the 2-sentence description in the image_description field."
)


class ImageGenData(BaseModel):
    """Output from image generation agent"""

    success: bool
    """Whether image description generation was successful"""

    image_description: str
    """The 2-sentence description for generating the image"""

    notes: str
    """Notes about the visual concept and design choices"""

    error_message: str | None = None
    """Error message if description generation failed"""


def new_imagegen_agent() -> Agent:
    """Create a new image generation agent."""
    return Agent(
        name="ImageGenAgent",
        instructions=IMAGE_GEN_PROMPT,
        model="gpt-4o-mini",  # Fast, cost-effective for description generation
        tools=[],  # No tools - just description generation
        output_type=ImageGenData,
    )
