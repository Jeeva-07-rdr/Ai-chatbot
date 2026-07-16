import json
import io
from django.http import HttpResponse
from django.conf import settings
from .models import Conversation, Message

# Try importing docx and reportlab safely (in case pip is still running)
try:
    from docx import Document
except ImportError:
    Document = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
except ImportError:
    SimpleDocTemplate = None


def export_conversation_to_json(conversation):
    messages = conversation.messages.all()
    data = {
        'chat_id': str(conversation.id),
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'messages': [
            {
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }
    return json.dumps(data, indent=2)


def export_conversation_to_markdown(conversation):
    messages = conversation.messages.all()
    md = f"# {conversation.title}\n"
    md += f"Chat ID: {conversation.id}\n"
    md += f"Date: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    for msg in messages:
        sender_name = "User" if msg.sender == 'user' else "UMI AI"
        md += f"### **{sender_name}** ({msg.created_at.strftime('%H:%M:%S')})\n"
        md += f"{msg.content}\n\n"
        md += "---\n\n"
    return md


def export_conversation_to_text(conversation):
    messages = conversation.messages.all()
    txt = f"=== CONVERSATION: {conversation.title} ===\n"
    txt += f"Chat ID: {conversation.id}\n"
    txt += f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for msg in messages:
        sender_name = "User" if msg.sender == 'user' else "UMI AI"
        txt += f"[{msg.created_at.strftime('%H:%M:%S')}] {sender_name}:\n{msg.content}\n\n"
    return txt


def export_conversation_to_docx(conversation):
    if Document is None:
        raise ImportError("python-docx is not installed on the system.")
        
    doc = Document()
    doc.add_heading(conversation.title, level=0)
    doc.add_paragraph(f"Chat ID: {conversation.id}")
    doc.add_paragraph(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph().add_run().add_break()
    
    for msg in conversation.messages.all():
        sender_name = "User" if msg.sender == 'user' else "UMI AI"
        p = doc.add_paragraph()
        run = p.add_run(f"{sender_name} ({msg.created_at.strftime('%H:%M:%S')}):\n")
        run.bold = True
        p.add_run(msg.content)
        doc.add_paragraph("—" * 30)
        
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def export_conversation_to_pdf(conversation):
    if SimpleDocTemplate is None:
        raise ImportError("reportlab is not installed on the system.")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        spaceAfter=12,
        textColor=HexColor('#4F46E5')
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        spaceAfter=24,
        textColor=HexColor('#6B7280')
    )
    
    user_header_style = ParagraphStyle(
        'UserHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        spaceBefore=12,
        spaceAfter=4,
        textColor=HexColor('#4F46E5')
    )
    
    ai_header_style = ParagraphStyle(
        'AIHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        spaceBefore=12,
        spaceAfter=4,
        textColor=HexColor('#111827')
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        spaceAfter=12,
        leading=14
    )
    
    story = []
    story.append(Paragraph(conversation.title, title_style))
    story.append(Paragraph(f"Chat ID: {conversation.id} | Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
    story.append(Spacer(1, 12))
    
    for msg in conversation.messages.all():
        if msg.sender == 'user':
            story.append(Paragraph(f"User ({msg.created_at.strftime('%H:%M:%S')}):", user_header_style))
        else:
            story.append(Paragraph(f"UMI AI ({msg.created_at.strftime('%H:%M:%S')}):", ai_header_style))
            
        story.append(Paragraph(msg.content.replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 6))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def render_markdown_to_html(text):
    """
    Renders raw markdown content into sanitized HTML with code syntax highlighting.
    
    Args:
        text (str): Raw Markdown string.
        
    Returns:
        str: Rendered HTML block.
    """
    import markdown
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'codehilite',
        'nl2br',
    ])
    return md.convert(text)


def extract_text_from_file(file_path, file_name):
    """
    Parses and extracts text from document files (PDF, DOCX, TXT, CSV, XLSX).
    """
    import os
    import csv
    
    ext = os.path.splitext(file_name)[1].lower()
    
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        elif ext == '.pdf':
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text.append(t)
            return "\n".join(text)
            
        elif ext == '.docx':
            import docx
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            for table in doc.tables:
                for row in table.rows:
                    text.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(text)
            
        elif ext == '.csv':
            text = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    text.append(", ".join(row))
            return "\n".join(text)
            
        elif ext in ['.xlsx', '.xls']:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            text = []
            for sheet in wb.worksheets:
                text.append(f"--- Sheet: {sheet.title} ---")
                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None for cell in row):
                        text.append(" | ".join(str(cell) if cell is not None else "" for cell in row))
            return "\n".join(text)
            
    except Exception as e:
        return f"[Error extracting text from {file_name}: {e}]"
        
    return ""
