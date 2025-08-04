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
class PDFGenerationResult:
    pdf_file_path: str
    success: bool
    error_message: Optional[str] = None


@activity.defn
async def generate_pdf(
    markdown_content: str,
    title: str = "Research Report",
    styling_options: Optional[StylingOptions] = None,
) -> PDFGenerationResult:
    """
    Generate PDF from markdown content with specified styling.

    Args:
        markdown_content: The markdown content to convert to PDF
        title: Title for the PDF document
        styling_options: Optional styling configurations

    Returns:
        PDFGenerationResult with pdf_bytes and success status
    """
    if not WEASYPRINT_AVAILABLE or weasyprint is None:
        return PDFGenerationResult(
            pdf_file_path="",
            success=False,
            error_message="weasyprint library not available",
        )

    try:
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content, extensions=["tables", "fenced_code", "toc"]
        )

        # Create complete HTML document with styling
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                {_get_default_css()}
                {_get_custom_css(styling_options)}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="document-title">{title}</h1>
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

    except Exception as e:
        return PDFGenerationResult(
            pdf_file_path="", success=False, error_message=str(e)
        )


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
