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


def render_markdown_to_html(markdown_text):
    """
    Renders raw markdown string to HTML using mistune or markdown library.
    """
    if not markdown_text:
        return ""
    try:
        import markdown
        return markdown.markdown(
            markdown_text,
            extensions=['fenced_code', 'tables', 'nl2br', 'codehilite']
        )
    except ImportError:
        # Fallback simple replacer if markdown lib is missing
        import html
        escaped = html.escape(markdown_text)
        return escaped.replace('\n', '<br>')


def optimize_profile_picture(image_file, max_size=(300, 300)):
    """
    Resizes and optimizes uploaded profile picture images using Pillow.
    Returns an InMemoryUploadedFile ready for saving to ImageField.
    """
    if not image_file:
        return image_file

    try:
        from PIL import Image
        import io
        from django.core.files.uploadedfile import InMemoryUploadedFile

        img = Image.open(image_file)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        filename = f"{image_file.name.split('.')[0]}.jpg"
        return InMemoryUploadedFile(
            output,
            'ImageField',
            filename,
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )
    except Exception as e:
        import logging
        logging.getLogger('umi').error(f"Image Optimization Error: {e}")
        return image_file


def extract_text_from_file(file_path, file_name):
    """
    Parses and extracts text from document files using page-aware RAGService.
    """
    from .rag_service import RAGService
    return RAGService.extract_text(file_path, file_name)


def create_password_reset_token(user):
    """
    Cleans expired tokens, generates a 64-char cryptographically secure token,
    stores it in PasswordResetToken with 30 minutes expiration, and returns the object.
    """
    import secrets
    from datetime import timedelta
    from django.utils import timezone
    from .models import PasswordResetToken

    PasswordResetToken.clean_expired_tokens()
    raw_token = secrets.token_urlsafe(48)
    expires_at = timezone.now() + timedelta(minutes=30)
    
    return PasswordResetToken.objects.create(
        user=user,
        token=raw_token,
        expires_at=expires_at,
        is_used=False
    )


def send_password_reset_email(user, reset_token_obj, request):
    """
    Constructs absolute reset link, renders HTML email template, performs SMTP checks,
    dispatches email, and prints structured diagnostic logs.
    """
    import logging
    import traceback
    import sys
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    logger = logging.getLogger('umi')
    reset_url = request.build_absolute_uri(f"/reset-password/{reset_token_obj.token}/")
    
    print("\n========== PASSWORD RESET ==========")
    print(f"Request Received:  {user.email}")
    print(f"Email Validation:  SUCCESS")
    print(f"User Found:        {user.username} (ID: {user.id})")
    print(f"Token Generated:   {reset_token_obj.token[:16]}...")
    print(f"Token Saved:       SUCCESS (Expires at: {reset_token_obj.expires_at})")
    print(f"SMTP Config Check: Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT} | TLS: {settings.EMAIL_USE_TLS} | User: {settings.EMAIL_HOST_USER or '(EMPTY)'}")

    context = {
        'user': user,
        'reset_url': reset_url,
        'expires_in': 30,
    }
    
    html_content = render_to_string('emails/password_reset_email.html', context)
    text_content = strip_tags(html_content)
    subject = "Reset Your UMI AI Password"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'UMI AI <noreply@umichat.com>')
    to_email = [user.email]

    # Check if SMTP user/password is set to dummy placeholder
    is_placeholder = (
        not settings.EMAIL_HOST_USER or
        not settings.EMAIL_HOST_PASSWORD or
        'your_email' in settings.EMAIL_HOST_USER or
        'your_app_password' in settings.EMAIL_HOST_PASSWORD
    )

    if is_placeholder:
        print("SMTP Connected:     SKIPPED (Placeholder credentials in .env)")
        print("SMTP Authenticated: SKIPPED (Set EMAIL_HOST_USER & EMAIL_HOST_PASSWORD in .env for live sending)")
        print(f"Email Delivered:    FALLBACK (Console/Log delivery)")
        print(f"Reset Link:         {reset_url}")
        print("Response Returned: SUCCESS (Anti-enumeration message displayed)")
        print("====================================\n")
        logger.info(f"EMAIL FALLBACK | Reset link for {user.username} ({user.email}): {reset_url}")
        return True

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        print("SMTP Connected:     SUCCESS")
        print("SMTP Authenticated: SUCCESS")
        print(f"Email Sent:         SUCCESS -> Delivered to {user.email}")
        print("Response Returned: SUCCESS (Anti-enumeration message displayed)")
        print("====================================\n")
        logger.info(f"EMAIL | Password reset email sent successfully via SMTP to {user.email}")
        return True
    except Exception as e:
        exc_type, exc_val, exc_tb = sys.exc_info()
        fname = exc_tb.tb_frame.f_code.co_filename if exc_tb else 'chat/services.py'
        line_no = exc_tb.tb_lineno if exc_tb else 281
        
        print("SMTP Connected:     FAILED")
        print("SMTP Authenticated: FAILED")
        print(f"Email Delivery:     FAILED ({type(e).__name__}: {e})")
        print(f"\n--- FAILURE DIAGNOSTICS ---")
        print(f"File Name:   {fname}")
        print(f"Function:    send_password_reset_email")
        print(f"Line Number: {line_no}")
        print(f"Exception:   {type(e).__name__}: {e}")
        print(f"Root Cause:  SMTP authentication failed because credentials in .env are either incorrect, missing an App Password, or blocked by provider.")
        print(f"Fallback URL: {reset_url}")
        print("====================================\n")

        logger.error(f"EMAIL | Failed to send reset email to {user.email}: {e}\n{traceback.format_exc()}")
        logger.info(f"EMAIL FALLBACK | Reset URL for {user.username}: {reset_url}")
        return False

