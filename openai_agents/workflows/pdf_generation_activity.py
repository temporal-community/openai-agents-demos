import base64
import os
from dataclasses import dataclass
from typing import Optional

import markdown
from pydantic import BaseModel
from temporalio import activity

# Set library path for WeasyPrint if not already set
if not os.environ.get("DYLD_FALLBACK_LIBRARY_PATH"):
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib"

try:
    import weasyprint

    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    weasyprint = None
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint not available: {e}")


class StylingOptions(BaseModel):
    """Styling options for PDF generation"""

    font_size: Optional[int] = None
    primary_color: Optional[str] = None


@dataclass
class ImageData:
    """Image data for embedding in PDF"""
    data: bytes  # Raw image bytes
    mime_type: str  # e.g., "image/png", "image/jpeg"
    caption: Optional[str] = None
    css_class: Optional[str] = "report-image"


@dataclass
class PDFGenerationResult:
    pdf_file_path: str
    success: bool
    error_message: Optional[str] = None


@activity.defn
async def generate_pdf(
    markdown_content: str,
    title: str = "Research Report",
    styling_options: Optional[StylingOptions] = None,
    image_path: Optional[str] = None,
) -> PDFGenerationResult:
    """
    Generate PDF from markdown content with optional hero image.

    Args:
        markdown_content: The markdown content to convert to PDF
        title: Title for the PDF document
        styling_options: Optional styling configurations
        image_path: Optional FILE PATH (not bytes) to image file to embed as hero image.
                   The image will be read from this path and embedded in the PDF.

    Returns:
        PDFGenerationResult with pdf_file_path and success status
    """
    if not WEASYPRINT_AVAILABLE or weasyprint is None:
        return PDFGenerationResult(
            pdf_file_path="",
            success=False,
            error_message="weasyprint library not available",
        )

    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_content, extensions=["tables", "fenced_code", "toc"]
    )

    # Load image from file path if provided
    hero_image = None
    if image_path:
        try:
            from pathlib import Path
            image_file = Path(image_path)
            if image_file.exists():
                with open(image_file, "rb") as f:
                    image_bytes = f.read()

                # Determine mime type from extension
                ext = image_file.suffix.lower().lstrip('.')
                mime_type = f"image/{ext}" if ext in ['png', 'jpg', 'jpeg', 'webp'] else "image/png"

                # Create ImageData from file
                hero_image = ImageData(
                    data=image_bytes,
                    mime_type=mime_type,
                    caption=None,  # Will be set by agent if needed
                    css_class="hero-image"
                )
                activity.logger.info(f"Loaded image from {image_path}: {len(image_bytes)} bytes")
            else:
                activity.logger.warning(f"Image file not found: {image_path}")
        except Exception as e:
            activity.logger.error(f"Failed to load image from {image_path}: {str(e)}")

    # Generate hero image HTML if provided
    hero_image_html = ""
    if hero_image and hero_image.data:
        data_uri = _image_to_base64_data_uri(hero_image.data, hero_image.mime_type)
        caption_html = ""
        if hero_image.caption:
            caption_html = f'<p class="image-caption">{hero_image.caption}</p>'

        hero_image_html = f'''
    <div class="image-container">
        <img src="{data_uri}" alt="Research illustration" class="{hero_image.css_class}">
        {caption_html}
    </div>
    '''

    # Create complete HTML document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            {_get_default_css()}
            {_get_image_css()}
            {_get_custom_css(styling_options)}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="document-title">{title}</h1>
            {hero_image_html}
            <div class="content">
                {html_content}
            </div>
        </div>
    </body>
    </html>
    """

    # Generate PDF and save to file
    import datetime
    from pathlib import Path

    # Create pdf_output directory if it doesn't exist
    pdf_output_dir = Path("pdf_output")
    pdf_output_dir.mkdir(exist_ok=True)

    # Create a unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"research_report_{timestamp}.pdf"
    pdf_path = pdf_output_dir / filename

    # Generate PDF directly to file
    weasyprint.HTML(string=full_html).write_pdf(str(pdf_path))

    return PDFGenerationResult(pdf_file_path=str(pdf_path), success=True)


def _get_default_css() -> str:
    """Get default CSS styling for PDF generation."""
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .container {
            margin: 0 auto;
        }
        
        .document-title {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-size: 28px;
        }
        
        .content h1 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 24px;
        }
        
        .content h2 {
            color: #34495e;
            margin-top: 25px;
            margin-bottom: 12px;
            font-size: 20px;
        }
        
        .content h3 {
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 18px;
        }
        
        .content p {
            margin-bottom: 15px;
            text-align: justify;
        }
        
        .content ul, .content ol {
            margin-bottom: 15px;
            padding-left: 30px;
        }
        
        .content li {
            margin-bottom: 8px;
        }
        
        .content blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
        }
        
        .content code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }
        
        .content pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }
        
        .content pre code {
            background-color: transparent;
            padding: 0;
        }
        
        .content table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        .content th, .content td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        .content th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .content tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        @page {
            margin: 1in;
            @bottom-center {
                content: counter(page);
                font-size: 12px;
                color: #666;
            }
        }
    """


def _image_to_base64_data_uri(image_bytes: bytes, mime_type: str) -> str:
    """
    Convert image bytes to a base64 data URI for HTML embedding.

    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type (e.g., 'image/png', 'image/jpeg')

    Returns:
        Data URI string ready for HTML embedding
    """
    # Encode to base64 and decode to UTF-8 string (critical for Python 3)
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:{mime_type};base64,{encoded}"


def _get_image_css() -> str:
    """CSS styling for images in PDFs."""
    return """
        /* Hero image under title */
        .hero-image {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 30px auto;
            page-break-inside: avoid;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Standard report images */
        .report-image {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            page-break-inside: avoid;
        }

        /* Images within content */
        .content img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15px 0;
        }

        /* High-quality image rendering */
        img {
            image-rendering: crisp-edges;
        }

        /* Image container */
        .image-container {
            margin: 20px 0;
            page-break-inside: avoid;
        }

        /* Image captions */
        .image-caption {
            text-align: center;
            font-style: italic;
            font-size: 0.9em;
            color: #666;
            margin-top: 8px;
            margin-bottom: 20px;
        }
    """


def _get_custom_css(styling_options: Optional[StylingOptions]) -> str:
    """Get custom CSS based on styling options."""
    if not styling_options:
        return ""

    custom_css = ""

    # Add custom font size
    if styling_options.font_size:
        custom_css += f"body {{ font-size: {styling_options.font_size}px; }}\n"

    # Add custom colors
    if styling_options.primary_color:
        custom_css += f"""
        .document-title, .content h1 {{ color: {styling_options.primary_color}; }}
        .document-title {{ border-bottom-color: {styling_options.primary_color}; }}
        .content blockquote {{ border-left-color: {styling_options.primary_color}; }}
        """

    return custom_css
