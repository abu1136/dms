import os
from datetime import datetime
from io import BytesIO
from copy import copy
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from html.parser import HTMLParser
from html import unescape

from app.config import get_settings

# Register Unicode fonts for special characters support
try:
    # Try to register DejaVu Sans for Unicode support (includes rupee symbol)
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Oblique', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-BoldOblique', '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'))
    
    # Register font family for automatic bold/italic substitution
    pdfmetrics.registerFontFamily('DejaVuSans',
        normal='DejaVuSans',
        bold='DejaVuSans-Bold',
        italic='DejaVuSans-Oblique',
        boldItalic='DejaVuSans-BoldOblique')
    
    UNICODE_FONT_AVAILABLE = True
except:
    # Fallback to Times if DejaVu not available
    UNICODE_FONT_AVAILABLE = False



class PDFGeneratorService:
    @staticmethod
    def generate_document_pdf(
        document_number: str,
        title: str,
        content: str,
        requested_by: str,
        template_path: str = None,
    ) -> bytes:
        """
        Generate a PDF document with optional template background.
        If template_path is provided, overlays content on the template.
        Otherwise, creates a simple document with company letterhead.
        Returns PDF as bytes.
        """
        if template_path and os.path.exists(template_path):
            return PDFGeneratorService._generate_with_template(
                document_number, title, content, requested_by, template_path
            )
        else:
            return PDFGeneratorService._generate_simple_pdf(
                document_number, title, content, requested_by
            )
    
    @staticmethod
    def _generate_with_template(
        document_number: str,
        title: str,
        content: str,
        requested_by: str,
        template_path: str,
    ) -> bytes:
        """Generate PDF by overlaying content on template with pagination and footer."""
        from datetime import datetime
        import pytz

        # Get local timezone (Asia/Kolkata)
        try:
            local_tz = pytz.timezone('Asia/Kolkata')
            local_time = datetime.now(local_tz)
        except:
            local_time = datetime.now()

        # Build content PDF using ReportLab flowables
        content_buffer = BytesIO()
        doc = SimpleDocTemplate(
            content_buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        styles = getSampleStyleSheet()
        elements = PDFGeneratorService._parse_html(content, styles)

        def add_footer(canvas_obj, doc_obj):
            canvas_obj.saveState()
            canvas_obj.setFont('Times-Roman', 8)
            page_num = canvas_obj.getPageNumber()
            footer_text = (
                f"Document: {document_number} | Page {page_num} | Generated: "
                f"{local_time.strftime('%d/%m/%Y %H:%M')}"
            )
            canvas_obj.drawCentredString(letter[0] / 2, 0.5 * inch, footer_text)
            canvas_obj.restoreState()

        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
        content_buffer.seek(0)

        # Merge each content page with the template page
        template_pdf = PdfReader(template_path)
        content_pdf = PdfReader(content_buffer)
        output = PdfWriter()

        template_page = template_pdf.pages[0]
        for page in content_pdf.pages:
            merged_page = copy(template_page)
            merged_page.merge_page(page)
            output.add_page(merged_page)

        result_buffer = BytesIO()
        output.write(result_buffer)
        result_buffer.seek(0)

        return result_buffer.getvalue()
    
    @staticmethod
    def _generate_simple_pdf(
        document_number: str,
        title: str,
        content: str,
        requested_by: str,
    ) -> bytes:
        """
        Generate a simple PDF document on company letterhead (no template).
        Supports CKEditor HTML including tables, lists, formatting.
        Returns PDF as bytes.
        """
        buffer = BytesIO()
        
        # Get local time
        from datetime import datetime
        import pytz
        
        try:
            local_tz = pytz.timezone('Asia/Kolkata')
            local_time = datetime.now(local_tz)
        except:
            local_time = datetime.now()
        
        # Custom page template to add footer
        def add_footer(canvas_obj, doc):
            canvas_obj.saveState()
            canvas_obj.setFont('Times-Roman', 8)
            page_num = canvas_obj.getPageNumber()
            footer_text = (
                f"Document: {document_number} | Page {page_num} | Generated: "
                f"{local_time.strftime('%d/%m/%Y %H:%M')}"
            )
            canvas_obj.drawCentredString(letter[0] / 2, 0.5 * inch, footer_text)
            canvas_obj.restoreState()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Company header style
        company_style = ParagraphStyle(
            'CompanyHeader',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Bold',
            textColor=colors.HexColor('#003366'),
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        
        # Company address style
        address_style = ParagraphStyle(
            'CompanyAddress',
            parent=styles['Normal'],
            fontSize=10,
            fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Roman',
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        
        # Document title style
        title_style = ParagraphStyle(
            'DocumentTitle',
            parent=styles['Heading2'],
            fontSize=14,
            fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Bold',
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        
        # Document info style
        info_style = ParagraphStyle(
            'DocumentInfo',
            parent=styles['Normal'],
            fontSize=10,
            fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Roman',
            alignment=TA_LEFT,
            spaceAfter=20,
        )
        
        # Add company letterhead
        elements.append(Paragraph(settings.company_name, company_style))
        elements.append(Paragraph(settings.company_address, address_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Add document info
        elements.append(Paragraph(f"<b>Document Number:</b> {document_number}", info_style))
        elements.append(Paragraph(f"<b>Date:</b> {local_time.strftime('%B %d, %Y')}", info_style))
        elements.append(Paragraph(f"<b>Requested By:</b> {requested_by}", info_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Add document title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Parse and add content with HTML support
        content_elements = PDFGeneratorService._parse_html(content, styles)
        elements.extend(content_elements)
        
        # Build PDF with footer
        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    @staticmethod
    def _parse_html(html_content: str, styles) -> list:
        """Parse HTML and convert to ReportLab flowables."""
        from bs4 import BeautifulSoup
        import re

        elements = []
        
        # Clean HTML to remove problematic styles while preserving content
        # Remove only span tags with complex style attributes that cause ReportLab issues
        html_content = re.sub(r'<span\s+[^>]*style\s*=\s*["\'][^"\']*font-family[^"\']*["\'][^>]*>([^<]*)</span>', r'\1', html_content)
        html_content = re.sub(r'<span\s+[^>]*>([^<]*)</span>', r'\1', html_content)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Define content styles with Times New Roman
        body_style = ParagraphStyle(
            'CKBody',
            parent=styles['BodyText'],
            fontSize=12,
            fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Roman',
            alignment=TA_JUSTIFY,
            spaceBefore=6,
            spaceAfter=6,
            leading=14,
        )
        
        heading_styles = {
            'h1': ParagraphStyle('CKH1', parent=body_style, fontSize=18, fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Bold', spaceBefore=12, spaceAfter=6),
            'h2': ParagraphStyle('CKH2', parent=body_style, fontSize=16, fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Bold', spaceBefore=12, spaceAfter=6),
            'h3': ParagraphStyle('CKH3', parent=body_style, fontSize=14, fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Bold', spaceBefore=12, spaceAfter=6),
        }
        
        # Track processed elements to avoid duplication
        processed_elements = set()
        
        # Process each element
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'ul', 'ol', 'table', 'figure', 'hr', 'br']):
            if element.name == 'table':
                # Handle tables
                table_data = []
                for row in element.find_all('tr'):
                    row_data = []
                    for cell in row.find_all(['td', 'th']):
                        cell_html = cell.decode_contents().strip() or '&nbsp;'
                        cell_html = cell_html.replace('<strong>', '<b>').replace('</strong>', '</b>')
                        cell_html = cell_html.replace('<em>', '<i>').replace('</em>', '</i>')
                        row_data.append(Paragraph(cell_html, ParagraphStyle('TableCell', parent=body_style, fontSize=10, fontName='DejaVuSans' if UNICODE_FONT_AVAILABLE else 'Times-Roman')))
                        # Mark all descendants as processed
                        for desc in cell.descendants:
                            processed_elements.add(id(desc))
                    if row_data:
                        table_data.append(row_data)
                
                if table_data:
                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
                        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 11),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 0.15 * inch))
                    processed_elements.add(id(element))
                    
            elif element.name in ['h1', 'h2', 'h3']:
                # Handle headings
                text = element.get_text(strip=True)
                if text:
                    elements.append(Paragraph(text, heading_styles[element.name]))
                    
            elif element.name in ['ul', 'ol']:
                # Handle lists
                for li in element.find_all('li', recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        list_style = ParagraphStyle('ListItem', parent=body_style, leftIndent=20, bulletIndent=10)
                        bullet = '•' if element.name == 'ul' else f'{li.parent.find_all("li").index(li) + 1}.'
                        elements.append(Paragraph(f"{bullet} {text}", list_style))
                        
            elif element.name == 'p':
                # Skip if already processed (e.g., inside a table)
                if id(element) in processed_elements:
                    continue
                    
                # Handle paragraphs with inline formatting
                html_text = str(element)
                
                # Skip if contains block elements like tables
                if element.find(['table', 'ul', 'ol']):
                    continue
                text_content = element.get_text(strip=True)
                if not text_content:
                    continue
                
                # Get inner HTML
                text = element.decode_contents()
                
                # Clean and convert HTML to ReportLab markup
                text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
                text = text.replace('<em>', '<i>').replace('</em>', '</i>')
                text = text.replace('<u>', '<u>').replace('</u>', '</u>')
                
                # Handle alignment - check both style attribute and inline styles
                para_style = body_style
                style_attr = element.get('style', '') or ''
                align_attr = element.get('align', '') or ''
                
                # Check for alignment in style attribute or align attribute
                if 'text-align:center' in style_attr or 'text-align: center' in style_attr or align_attr == 'center':
                    para_style = ParagraphStyle('Center', parent=body_style, alignment=TA_CENTER)
                elif 'text-align:right' in style_attr or 'text-align: right' in style_attr or align_attr == 'right':
                    para_style = ParagraphStyle('Right', parent=body_style, alignment=TA_RIGHT)
                elif 'text-align:justify' in style_attr or 'text-align: justify' in style_attr or align_attr == 'justify':
                    para_style = ParagraphStyle('Justify', parent=body_style, alignment=TA_JUSTIFY)
                elif 'text-align:left' in style_attr or 'text-align: left' in style_attr or align_attr == 'left':
                    para_style = ParagraphStyle('Left', parent=body_style, alignment=TA_LEFT)
                
                if text.strip():
                    try:
                        elements.append(Paragraph(text, para_style))
                    except Exception as e:
                        # Fallback to plain text if HTML parsing fails
                        plain_text = element.get_text()
                        if plain_text.strip():
                            elements.append(Paragraph(plain_text, para_style))

            elif element.name == 'br':
                # Handle line breaks
                elements.append(Spacer(1, 0.1 * inch))

            if element.name in ['figure', 'hr']:
                classes = ' '.join(element.get('class', []))
                style = element.get('style', '') or ''
                if 'page-break' in classes or 'page-break-after' in style:
                    elements.append(PageBreak())
        
        return elements
    
    @staticmethod
    def save_pdf(pdf_bytes: bytes, file_path: str) -> None:
        """Save PDF bytes to file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
