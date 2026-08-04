import json
import uuid
import time
import logging
import traceback
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.cache import cache

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.db import transaction

from .models import UserSettings, UserProfile, Conversation, Message, Attachment
from .forms import (
    LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm,
    UserProfileForm, UserSettingsForm
)
from . import services
from . import ai_service

logger = logging.getLogger('umi')


# --- Enterprise Authentication Views ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat')

    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Session Expiration based on Remember Me
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(2592000)  # 30 days
            else:
                request.session.set_expiry(0)  # Browser close
                
            logger.info(f"AUTH | Login successful | User: {user.username}")
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            
            if next_url:
                return redirect(next_url)
            return redirect('chat')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form, 'next_url': next_url})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('chat')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()

                # Create UserProfile
                UserProfile.objects.create(user=user)

                # Create UserSettings & process profile pic
                user_settings = UserSettings.objects.create(user=user)
                if request.FILES.get('profile_pic'):
                    optimized = services.optimize_profile_picture(request.FILES['profile_pic'])
                    user_settings.profile_pic = optimized
                    user_settings.save()

            login(request, user)
            logger.info(f"AUTH | Account registered & logged in | User: {user.username}")
            messages.success(request, f"Account created successfully! Welcome to UMI, {user.username}.")
            return redirect('chat')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('chat')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['email'].strip()
            
            # Rate limiting check (max 3 requests per 15 mins per IP/email)
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            rate_key = f"pwd_reset_rate_{client_ip}_{identifier}"
            request_count = cache.get(rate_key, 0)
            
            if request_count >= 3:
                logger.warning(f"AUTH | Rate limit exceeded for password reset request | Input: {identifier} | IP: {client_ip}")
                messages.error(request, "Too many password reset requests. Please wait 15 minutes before trying again.")
                return render(request, 'forgot_password.html', {'form': form})
                
            cache.set(rate_key, request_count + 1, 900)  # 15 minutes
            
            # Search for user by email address OR username
            user = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
            if user and user.email:
                # Create token & send email
                reset_token_obj = services.create_password_reset_token(user)
                services.send_password_reset_email(user, reset_token_obj, request)
                logger.info(f"AUTH | Password reset link issued for user: {user.username} ({user.email})")
                from chat.repositories import AnalyticsRepository
                AnalyticsRepository.log_runtime('INFO', f"Password reset requested for {user.email} (User: {user.username})")
            else:
                logger.info(f"AUTH | Password reset requested for non-registered input: {identifier}")
                from chat.repositories import AnalyticsRepository
                AnalyticsRepository.log_runtime('WARNING', f"Password reset attempt for non-registered input: {identifier}")

            # Anti-enumeration response (same message regardless of existence)
            messages.info(request, "If an account matching this email or username exists, a password reset link has been sent to the registered email address.")
            return render(request, 'forgot_password.html', {'form': ForgotPasswordForm()})
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})


def reset_password_view(request, token):
    from chat.models import PasswordResetToken
    from chat.repositories import AnalyticsRepository

    reset_token_obj = PasswordResetToken.objects.filter(token=token).first()

    if not reset_token_obj or not reset_token_obj.is_valid():
        logger.warning(f"AUTH | Invalid or expired password reset token attempt: {token[:12] if token else 'None'}...")
        AnalyticsRepository.log_runtime('WARNING', f"Invalid or expired password reset token attempt: {token[:12] if token else 'None'}...")
        messages.error(request, "This password reset link is invalid, has expired, or has already been used. Please request a new link.")
        return redirect('forgot_password')

    user = reset_token_obj.user

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Set new password securely using Django PBKDF2 hashing
                user.set_password(form.cleaned_data['new_password'])
                user.save()

                # Mark token as used
                reset_token_obj.is_used = True
                reset_token_obj.save()

                # Invalidate all existing login sessions for user
                try:
                    from django.contrib.sessions.models import Session
                    for session in Session.objects.all():
                        try:
                            session_data = session.get_decoded()
                            if session_data.get('_auth_user_id') == str(user.id):
                                session.delete()
                        except Exception:
                            pass
                except Exception:
                    pass

            logger.info(f"AUTH | Password reset successfully completed for user: {user.username}")
            AnalyticsRepository.log_runtime('INFO', f"Password reset successfully completed for user: {user.username}")
            messages.success(request, "Your password has been reset successfully! Please sign in with your new password.")
            return redirect('login')
    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': form, 'token': token, 'valid_user': user.username})


def logout_view(request):
    username = request.user.username if request.user.is_authenticated else 'Anonymous'
    user_id = request.user.id if request.user.is_authenticated else None
    
    if user_id:
        invalidate_sidebar_cache(user_id)

    logout(request)
    request.session.flush()
    logger.info(f"AUTH | User logged out & session flushed | User: {username}")
    
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def remove_avatar_view(request):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    
    if user_settings.profile_pic:
        try:
            if os.path.exists(user_settings.profile_pic.path):
                os.remove(user_settings.profile_pic.path)
        except Exception as e:
            logger.warning(f"Avatar file remove error: {e}")
        user_settings.profile_pic = None
        user_settings.save()
        logger.info(f"DB | Avatar removed for user: {user.username}")
        messages.success(request, "Profile picture removed.")

    invalidate_sidebar_cache(user.id)
    return redirect('settings')


def get_dev_user(request):
    """
    Helper function to automatically sign in a development user.
    This ensures the chatbot is completely usable out-of-the-box
    without requiring manual signup or login setups first.
    """
    user, created = User.objects.get_or_create(
        username='johndoe',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        logger.info(f"AUTH | Auto-created dev user: {user.username} (ID: {user.id})")
        
    # Ensure UserSettings exists
    UserSettings.objects.get_or_create(user=user)
    
    if not request.user.is_authenticated:
        login(request, user)
        logger.info(f"AUTH | Auto-login for dev user: {user.username}")
    return user


def invalidate_sidebar_cache(user_id):
    """Utility to clear sidebar cache for a user when conversation state updates."""
    cache.delete(f"sidebar_context_{user_id}")


import threading

def run_async_summarizer(conversation_id, provider, model):
    """
    Spawns a background thread to summarize older parts of the conversation.
    This runs asynchronously to avoid blocking the user request.
    """
    def summarizer_task():
        try:
            # Local imports inside the thread to be fully safe
            from chat.models import Conversation
            from chat import ai_service
            
            conversation = Conversation.objects.filter(id=conversation_id).first()
            if not conversation:
                return
                
            all_msgs = conversation.messages.order_by('created_at')
            total_count = all_msgs.count()
            if total_count <= 10:
                return
                
            # Summarize everything older than the last 10 messages
            older_msgs = all_msgs[:total_count - 10]
            older_count = older_msgs.count()
            
            # Check if this exact older count has already been summarized
            count_cache_key = f"conv_summary_count_{conversation.id}"
            last_count = cache.get(count_cache_key)
            if last_count == older_count:
                return
                
            history_text = []
            for msg in older_msgs:
                role_name = "User" if msg.sender == 'user' else "Assistant"
                history_text.append(f"{role_name}: {msg.content}")
            history_str = "\n".join(history_text)
            
            summary_prompt = (
                "Summarize the key points of the preceding conversation history briefly in 2-3 sentences. "
                "Keep it highly compact and direct. Do not include introductory phrases. "
                "History to summarize:\n\n" + history_str
            )
            
            summary_text = ""
            for chunk in ai_service.stream_ai_response(
                provider=provider,
                model=model,
                prompt=summary_prompt,
                history=[],
                system_prompt="You are a helpful assistant that summarizes conversation history key details."
            ):
                summary_text += chunk
                
            if summary_text.strip():
                summary_cache_key = f"conv_summary_{conversation.id}"
                cache.set(summary_cache_key, summary_text.strip(), 86400 * 7) # Cache for 7 days
                cache.set(count_cache_key, older_count, 86400 * 7)
                logger.info(f"AI | Cached summary updated for Conversation {conversation.id} | Summarized {older_count} messages")
        except Exception as e:
            logger.error(f"AI | Summarization background thread failed: {e}")

    threading.Thread(target=summarizer_task, daemon=True).start()


def get_sidebar_context(user):
    """
    Helper to generate categorized chat history for the sidebar.
    Caches results per user and invalidates when a conversation changes.
    """
    cache_key = f"sidebar_context_{user.id}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Fetch pinned conversations directly in one query
    pinned_chats = list(Conversation.objects.filter(
        user=user,
        is_deleted=False,
        is_archived=False,
        is_pinned=True
    ).order_by('-updated_at'))

    # Fetch unpinned conversations, selecting only the columns needed for rendering
    unpinned_chats = Conversation.objects.filter(
        user=user,
        is_deleted=False,
        is_archived=False,
        is_pinned=False
    ).only('id', 'title', 'updated_at')

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    
    today_chats = []
    yesterday_chats = []
    seven_days_chats = []
    older_chats = []
    
    for chat in unpinned_chats:
        chat_date = chat.updated_at.date()
        if chat_date == today:
            today_chats.append(chat)
        elif chat_date == yesterday:
            yesterday_chats.append(chat)
        elif chat_date >= seven_days_ago:
            seven_days_chats.append(chat)
        else:
            older_chats.append(chat)
            
    sidebar_ctx = {
        'pinned_chats': pinned_chats,
        'today_chats': today_chats,
        'yesterday_chats': yesterday_chats,
        'seven_days_chats': seven_days_chats,
        'older_chats': older_chats,
    }
    # Cache for 10 minutes
    cache.set(cache_key, sidebar_ctx, 600)
    return sidebar_ctx


def chat_view(request):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    sidebar_ctx = get_sidebar_context(user)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    
    context = {
        'page_title': 'New Chat',
        'user_settings': user_settings,
        **sidebar_ctx
    }
    return render(request, 'chat.html', context)


def chat_detail_view(request, chat_id):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    try:
        conversation = Conversation.objects.get(id=chat_id, user=user, is_deleted=False)
    except (Conversation.DoesNotExist, Exception):
        logger.warning(f"DB | Chat not found or deleted | ID: {chat_id} | User: {user.username}")
        return redirect('chat')
    
    sidebar_ctx = get_sidebar_context(user)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    
    # Load all messages and render AI markdown content with local cache
    chat_messages = conversation.messages.all()
    for msg in chat_messages:
        if msg.sender == 'ai':
            cache_key = f"msg_rendered_{msg.id}"
            rendered = cache.get(cache_key)
            if rendered is None:
                rendered = services.render_markdown_to_html(msg.content)
                cache.set(cache_key, rendered, 86400 * 7) # Cache for 7 days
            msg.rendered_content = rendered
        else:
            msg.rendered_content = msg.content
            
    context = {
        'page_title': conversation.title,
        'active_chat': conversation,
        'chat_messages': chat_messages,
        'user_settings': user_settings,
        **sidebar_ctx
    }
    return render(request, 'chat.html', context)


def new_chat(request):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    conversation = Conversation.objects.create(user=user, title="New Chat")
    logger.info(f"DB | Conversation created | ID: {conversation.id} | User: {user.username}")
    return redirect('chat_detail', chat_id=conversation.id)





def send_message(request, chat_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    from .performance_tracer import PerformanceTracer
    tracer = PerformanceTracer("Chat Send Message")
    
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    tracer.mark('Authentication')
    
    conversation = get_object_or_404(Conversation, id=chat_id, user=user)
    tracer.mark('Conversation Retrieval')
    
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    edit_message_id = data.get('edit_message_id')
    attachment_ids = data.get('attachment_ids', [])
    
    if not content and not attachment_ids:
        logger.warning(f"CHAT | Empty message rejected | Conversation: {chat_id} | User: {user.username}")
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
    if not content:
        # Fallback if only attachments were uploaded
        first_att = Attachment.objects.filter(id__in=attachment_ids).first()
        content = f"Analyze file: {first_att.file_name}" if first_att else "Analyze files"
        
    if edit_message_id:
        # Editing an existing message: update its content
        user_msg = get_object_or_404(Message, id=edit_message_id, conversation=conversation)
        user_msg.content = content
        user_msg.save()
        
        # Wipe out all future messages in this conversation
        conversation.messages.filter(created_at__gt=user_msg.created_at).delete()
    else:
        # Save User message
        user_msg = Message.objects.create(conversation=conversation, sender='user', content=content)
    
    tracer.mark('Database Update')
        
    # Link any newly uploaded attachments to user message and conversation
    if attachment_ids:
        attachments = Attachment.objects.filter(id__in=attachment_ids)
        attachments.update(message=user_msg, conversation=conversation)
        logger.info(f"DB | Linked {len(attachment_ids)} attachment(s) to conversation {conversation.id}")
        
    user_settings_temp, _ = UserSettings.objects.get_or_create(user=user)
    tracer.mark('Session Lookup')
        
    # Process files / Knowledge retrieval
    files_context = ""
    multimodal_parts = []
    
    # Retrieve all attachments for this conversation (including past and newly attached)
    all_attachments = Attachment.objects.filter(conversation=conversation)
        
    for attachment in all_attachments:
        file_path = attachment.file.path
        file_name = attachment.file_name
        file_type = attachment.file_type
        
        if file_type.startswith('image/') and user_settings_temp.ai_provider == 'gemini':
            try:
                with open(file_path, 'rb') as f:
                    img_bytes = f.read()
                multimodal_parts.append({
                    'bytes': img_bytes,
                    'mime_type': file_type
                })
            except Exception as e:
                files_context += f"\n[Error loading image {file_name}: {e}]\n"
        else:
            # Parse text from PDFs, DOCX, CSV, Excel, TXT, Code files (cached to prevent repeated I/O)
            att_cache_key = f"attachment_text_{attachment.id}"
            parsed_text = cache.get(att_cache_key)
            if parsed_text is not None:
                tracer.record_cache_hit()
            else:
                tracer.record_cache_miss()
                parsed_text = services.extract_text_from_file(file_path, file_name)
                cache.set(att_cache_key, parsed_text, 86400 * 7) # Cache for 7 days
            if parsed_text:
                from .rag_service import RAGService
                retrieved = RAGService.retrieve_context(content, parsed_text, file_name)
                files_context += f"\n\n{retrieved}\n\n"
                
    tracer.mark('Knowledge Retrieval')
    
    prompt_content = content
    if files_context.strip():
        from .rag_service import RAGService
        prompt_content = RAGService.build_rag_prompt(content, files_context.strip())
        
    tracer.mark('Prompt Construction')
        
    # Fetch last 10 chronological messages (excluding current message) to optimize context length
    past_messages = list(conversation.messages.filter(id__lt=user_msg.id).order_by('-created_at')[:10])
    past_messages.reverse()
    
    history = []
    # Prepend cached summary if it exists
    summary_cache_key = f"conv_summary_{conversation.id}"
    summary = cache.get(summary_cache_key)
    if summary:
        tracer.record_cache_hit()
        history.append({
            'role': 'system',
            'content': f"Summary of older conversation history: {summary}"
        })
    else:
        tracer.record_cache_miss()
        
    for msg in past_messages:
        history.append({
            'role': 'user' if msg.sender == 'user' else 'assistant',
            'content': msg.content
        })
        
    tracer.mark('Conversation Compression')
    tracer.mark('Memory Retrieval')
        
    user_settings = user_settings_temp
    system_prompt = ai_service.get_system_prompt_for_style(
        user_settings.response_style,
        user_settings.ai_provider,
        user_settings.ai_model
    )
    
    tracer.mark('Provider Selection')
    tracer.mark('Cache Lookup')
    
    # Calculate estimated tokens safely
    prompt_words = (
        len((prompt_content or '').split()) +
        len((system_prompt or '').split()) +
        sum(len((m.get('content') or '').split()) for m in history)
    )
    
    if user_settings.streaming:
        # Streaming response pipeline
        from django.http import StreamingHttpResponse
        from django.template.loader import render_to_string
        import time
        
        def event_stream_generator():
            accumulated_text = ""
            first_token_received = False
            start_time = time.time()
            tracer.mark('Send Request To AI')
            
            # Send metadata (model name and title)
            yield f"data: {json.dumps({'type': 'meta', 'chat_title': conversation.title, 'provider': user_settings.ai_provider, 'model': user_settings.ai_model})}\n\n"
            
            try:
                for chunk in ai_service.stream_ai_response(
                    provider=user_settings.ai_provider,
                    model=user_settings.ai_model,
                    prompt=prompt_content,
                    history=history,
                    system_prompt=system_prompt,
                    multimodal_parts=multimodal_parts,
                    response_style=user_settings.response_style
                ):
                    if not first_token_received and chunk:
                        first_token_received = True
                        tracer.mark('Time To First Token')
                    accumulated_text += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            except GeneratorExit:
                logger.warning(f"AI | Stream aborted by user | Conversation: {conversation.id}")
                pass
                
            duration = round(time.time() - start_time, 2)
            tracer.mark('Generation Time')
            tracer.mark('Streaming Time')
            
            if not accumulated_text.strip():
                accumulated_text = "No response was generated or generation was canceled."
                logger.warning(f"AI | Empty response generated | Conversation: {conversation.id} | Duration: {duration}s")
            else:
                # Enforce UMI identity on small models post-generation
                if any(q in content.lower() for q in ["who are you", "what are you", "your name", "who created you"]):
                    if "language model" in accumulated_text.lower() or "assistant" in accumulated_text.lower() or "qwen" in accumulated_text.lower():
                        accumulated_text = "I am UMI, a premium, intelligent AI chat assistant. I am here to help you with code, writing, and any questions you have!"
                
            # Save the final AI response to the database
            ai_msg = Message.objects.create(
                conversation=conversation, 
                sender='ai', 
                content=accumulated_text
            )
            conversation.save() # Touch
            tracer.mark('Database Update')
            
            rendered_reply = services.render_markdown_to_html(ai_msg.content)
            ai_html = render_to_string('components/message.html', {
                'is_user': False,
                'content': rendered_reply,
                'time': ai_msg.created_at.strftime('%H:%M')
            })
            
            yield f"data: {json.dumps({'type': 'done', 'ai_html': ai_html, 'duration': duration, 'message_id': ai_msg.id, 'user_message_id': user_msg.id})}\n\n"
            
            tracer.mark('Response Complete')
            
            # Record token metrics
            output_words = len(accumulated_text.split())
            tracer.set_tokens(int(prompt_words * 1.3), int(output_words * 1.3))
            tracer.add_api_time(duration)
            tracer.generate_report()
            
            # Trigger background summarizer for older context
            run_async_summarizer(conversation.id, user_settings.ai_provider, user_settings.ai_model)
            # Invalidate user sidebar cache
            invalidate_sidebar_cache(user.id)
            
        response = StreamingHttpResponse(event_stream_generator(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no' # Disable Nginx buffering
        return response
        
    else:
        # Non-streaming response pipeline
        from django.template.loader import render_to_string
        import time
        start_time = time.time()
        
        reply_content = ""
        try:
            for chunk in ai_service.stream_ai_response(
                provider=user_settings.ai_provider,
                model=user_settings.ai_model,
                prompt=prompt_content,
                history=history,
                system_prompt=system_prompt,
                multimodal_parts=multimodal_parts,
                response_style=user_settings.response_style
            ):
                reply_content += chunk
        except Exception as e:
            reply_content = f"An unexpected error occurred: {e}"
            logger.error(f"AI | Non-streaming error | {type(e).__name__}: {e}\n{traceback.format_exc()}")
            
        duration = round(time.time() - start_time, 2)
        if not reply_content.strip():
            reply_content = "No response generated."
        else:
            # Enforce UMI identity on small models post-generation
            if any(q in content.lower() for q in ["who are you", "what are you", "your name", "who created you"]):
                if "language model" in reply_content.lower() or "assistant" in reply_content.lower() or "qwen" in reply_content.lower():
                    reply_content = "I am UMI, a premium, intelligent AI chat assistant. I am here to help you with code, writing, and any questions you have!"
            
        # Save AI message
        ai_msg = Message.objects.create(conversation=conversation, sender='ai', content=reply_content)
        conversation.save() # Touch
        
        logger.success(
            f"AI | Response complete (non-streaming)\n"
            f"  Provider: {user_settings.ai_provider}\n"
            f"  Model: {user_settings.ai_model}\n"
            f"  Duration: {duration}s\n"
            f"  Characters: {len(reply_content)}\n"
            f"  Conversation: #{conversation.id}"
        )
        
        user_html = render_to_string('components/message.html', {
            'is_user': True,
            'content': user_msg.content,
            'time': user_msg.created_at.strftime('%H:%M')
        })
        
        rendered_reply = services.render_markdown_to_html(ai_msg.content)
        ai_html = render_to_string('components/message.html', {
            'is_user': False,
            'content': rendered_reply,
            'time': ai_msg.created_at.strftime('%H:%M')
        })
        
        # Trigger background summarizer for older context
        run_async_summarizer(conversation.id, user_settings.ai_provider, user_settings.ai_model)
        # Invalidate user sidebar cache
        invalidate_sidebar_cache(user.id)
        
        return JsonResponse({
            'user_html': user_html,
            'ai_html': ai_html,
            'chat_title': conversation.title,
            'duration': duration,
            'message_id': ai_msg.id,
            'user_message_id': user_msg.id
        })


def rename_chat(request, chat_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    conversation = get_object_or_404(Conversation, id=chat_id, user=user)
    
    data = json.loads(request.body)
    new_title = data.get('title', '').strip()
    if new_title:
        old_title = conversation.title
        conversation.title = new_title
        conversation.save()
        logger.info(f"DB | Chat renamed | ID: {conversation.id} | '{old_title}' -> '{new_title}' | User: {user.username}")
        invalidate_sidebar_cache(user.id)
        return JsonResponse({'success': True, 'title': conversation.title})
    return JsonResponse({'error': 'Title cannot be empty'}, status=400)


def delete_chat(request, chat_id):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    conversation = get_object_or_404(Conversation, id=chat_id, user=user)
    conversation.is_deleted = True
    conversation.save()
    
    logger.info(f"DB | Chat deleted | ID: {conversation.id} | Title: '{conversation.title}' | User: {user.username}")
    invalidate_sidebar_cache(user.id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'json' in request.headers.get('Accept', ''):
        return JsonResponse({'success': True, 'chat_id': str(chat_id)})
    return redirect('chat')


def pin_chat(request, chat_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    conversation = get_object_or_404(Conversation, id=chat_id, user=user)
    
    conversation.is_pinned = not conversation.is_pinned
    conversation.save()
    
    invalidate_sidebar_cache(user.id)
    return JsonResponse({'success': True, 'is_pinned': conversation.is_pinned})


def archive_chat(request, chat_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    conversation = get_object_or_404(Conversation, id=chat_id, user=user)
    
    conversation.is_archived = not conversation.is_archived
    conversation.save()
    
    invalidate_sidebar_cache(user.id)
    return JsonResponse({'success': True, 'is_archived': conversation.is_archived})


def duplicate_chat(request, chat_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    src_chat = get_object_or_404(Conversation, id=chat_id, user=user)
    
    # Clone conversation
    new_chat = Conversation.objects.create(
        user=user,
        title=f"Copy of {src_chat.title}"
    )
    
    # Clone messages
    messages_to_create = []
    for msg in src_chat.messages.all():
        messages_to_create.append(Message(
            conversation=new_chat,
            sender=msg.sender,
            content=msg.content
        ))
    Message.objects.bulk_create(messages_to_create)
    
    invalidate_sidebar_cache(user.id)
    return JsonResponse({'success': True, 'new_chat_url': f'/chat/{new_chat.id}/'})


def reorder_pins(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    invalidate_sidebar_cache(user.id)
    return JsonResponse({'success': True})


def search_chats(request):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
        
    # Search in titles and message contents
    matched_msgs = Message.objects.filter(
        conversation__user=user,
        conversation__is_deleted=False,
        conversation__is_archived=False
    ).filter(
        Q(content__icontains=query) | Q(conversation__title__icontains=query)
    ).select_related('conversation')
    
    results = []
    seen_conversations = set()
    
    for msg in matched_msgs:
        chat = msg.conversation
        if chat.id in seen_conversations:
            continue
        seen_conversations.add(chat.id)
        
        # Simple snippet highlight logic
        content = msg.content
        hl_title = chat.title
        hl_snippet = content
        
        if query.lower() in chat.title.lower():
            start = chat.title.lower().find(query.lower())
            hl_title = f"{chat.title[:start]}<mark class='px-1 rounded bg-warning text-dark'>{chat.title[start:start+len(query)]}</mark>{chat.title[start+len(query):]}"
            
        if query.lower() in content.lower():
            start = content.lower().find(query.lower())
            snippet_start = max(0, start - 30)
            snippet_end = min(len(content), start + len(query) + 50)
            prefix = "..." if snippet_start > 0 else ""
            suffix = "..." if snippet_end < len(content) else ""
            raw_snippet = content[snippet_start:snippet_end]
            hl_snippet = f"{prefix}{raw_snippet.replace(query, f'<mark class=bg-warning>{query}</mark>')}{suffix}"
        
        results.append({
            'chat_id': str(chat.id),
            'title': chat.title,
            'highlighted_title': hl_title,
            'snippet': hl_snippet,
            'updated_at': chat.updated_at.strftime('%Y-%m-%d')
        })
        
    return JsonResponse({'results': results})


def export_chat(request, chat_id, format_type):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    conversation = get_object_or_404(Conversation, id=chat_id, user=user)
    
    if format_type == 'json':
        response_data = services.export_conversation_to_json(conversation)
        response = HttpResponse(response_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="chat_{conversation.id}.json"'
        return response
        
    elif format_type in ('markdown', 'md'):
        response_data = services.export_conversation_to_markdown(conversation)
        response = HttpResponse(response_data, content_type='text/markdown')
        response['Content-Disposition'] = f'attachment; filename="chat_{conversation.id}.md"'
        return response
        
    elif format_type == 'txt':
        response_data = services.export_conversation_to_text(conversation)
        response = HttpResponse(response_data, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="chat_{conversation.id}.txt"'
        return response
        
    elif format_type == 'docx':
        try:
            response_data = services.export_conversation_to_docx(conversation)
            response = HttpResponse(response_data, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename="chat_{conversation.id}.docx"'
            return response
        except Exception as e:
            return HttpResponse(f"Error generating Word document: {e}", status=500)
            
    elif format_type == 'pdf':
        try:
            response_data = services.export_conversation_to_pdf(conversation)
            response = HttpResponse(response_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="chat_{conversation.id}.pdf"'
            return response
        except Exception as e:
            return HttpResponse(f"Error generating PDF: {e}", status=500)
            
    return HttpResponse("Invalid export format requested", status=400)


def settings_view(request):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    sidebar_ctx = get_sidebar_context(user)
    
    profile_form = UserProfileForm(instance=user)
    settings_form = UserSettingsForm(instance=user_settings)
    
    context = {
        'page_title': 'Settings',
        'profile_form': profile_form,
        'settings_form': settings_form,
        'user_settings': user_settings,
        **sidebar_ctx
    }
    return render(request, 'settings.html', context)


def save_profile(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    
    form = UserProfileForm(request.POST, instance=user)
    if form.is_valid():
        form.save()
        
        # Handle profile picture upload from profile form if provided
        if request.FILES.get('profile_pic'):
            optimized = services.optimize_profile_picture(request.FILES['profile_pic'])
            user_settings.profile_pic = optimized
            user_settings.save()
            
        logger.info(f"DB | Profile updated | User: {user.username} (ID: {user.id})")
        messages.success(request, "Profile details updated successfully.")
        invalidate_sidebar_cache(user.id)
        return JsonResponse({'success': True, 'message': 'Profile details saved successfully.'})
    else:
        errors = {field: errors[0] for field, errors in form.errors.items()}
        logger.warning(f"DB | Profile update failed | User: {user.username} | Errors: {errors}")
        return JsonResponse({'success': False, 'errors': errors}, status=400)


def save_preferences(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    
    form = UserSettingsForm(request.POST, request.FILES, instance=user_settings)
    if form.is_valid():
        form.save()
        logger.info(
            f"DB | Settings updated | User: {user.username}\n"
            f"  Provider: {user_settings.ai_provider} | Model: {user_settings.ai_model}"
        )
        invalidate_sidebar_cache(user.id)
        return JsonResponse({'success': True, 'message': 'Preferences saved successfully.'})
    else:
        errors = {field: errors[0] for field, errors in form.errors.items()}
        logger.warning(f"DB | Settings update failed | User: {user.username} | Errors: {errors}")
        return JsonResponse({'success': False, 'errors': errors}, status=400)


def delete_account(request):
    if request.method != 'POST':
        return redirect('settings')

    user = request.user if request.user.is_authenticated else get_dev_user(request)
    password = request.POST.get('password', '')

    if not user.check_password(password):
        messages.error(request, "Account deletion failed: Incorrect password provided.")
        logger.warning(f"AUTH | Failed account deletion attempt (wrong password) | User: {user.username}")
        return redirect('settings')

    username = user.username
    user_id = user.id

    with transaction.atomic():
        # Delete user files from disk
        attachments = Attachment.objects.filter(user=user)
        for att in attachments:
            try:
                if att.file and os.path.exists(att.file.path):
                    os.remove(att.file.path)
            except Exception as e:
                logger.warning(f"File delete cleanup error: {e}")
        
        user_settings = getattr(user, 'settings', None)
        if user_settings and user_settings.profile_pic:
            try:
                if os.path.exists(user_settings.profile_pic.path):
                    os.remove(user_settings.profile_pic.path)
            except Exception as e:
                logger.warning(f"Profile pic cleanup error: {e}")

        # Delete database records
        user.conversations.all().delete()
        user.delete()

    logout(request)
    request.session.flush()
    logger.warning(f"AUTH | Account completely deleted from database | User: {username} (ID: {user_id})")
    messages.info(request, "Your UMI account and all stored data have been permanently deleted.")
    return redirect('login')


def clear_history(request):
    if request.method != 'POST':
        return redirect('settings')
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    count = Conversation.objects.filter(user=user, is_deleted=False).count()
    Conversation.objects.filter(user=user).update(is_deleted=True)
    logger.info(f"DB | Chat history cleared | {count} conversation(s) deleted | User: {user.username}")
    invalidate_sidebar_cache(user.id)
    return redirect('chat')


def help_view(request):
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    sidebar_ctx = get_sidebar_context(user)
    
    context = {
        'page_title': 'Help Center',
        'user_settings': user_settings,
        **sidebar_ctx
    }
    return render(request, 'help.html', context)


def poll_notifications(request):
    """
    Returns simulated recent activities/notifications.
    """
    notifications = [
        {'id': 1, 'type': 'update', 'text': 'UMI updated to standard v1.0.0.'},
        {'id': 2, 'type': 'activity', 'text': 'You exported "Explain Python decorators".'},
        {'id': 3, 'type': 'alert', 'text': 'Streaming response latency optimized.'}
    ]
    return JsonResponse({
        'notifications': notifications,
        'unread_count': len(notifications)
    })


def logout_view(request):
    username = request.user.username if request.user.is_authenticated else 'Anonymous'
    logger.info(f"AUTH | User logged out | User: {username}")
    logout(request)
    return redirect('/')


# --- Helper reply engine ---

def generate_smart_reply(prompt):
    p_lower = prompt.lower()
    
    if "python" in p_lower:
        return (
            "Python is a high-level, interpreted programming language known for its readability and simplicity. "
            "Here is how you write a basic function with type hinting:\n\n"
            "```python\n"
            "def calculate_total(price: float, tax: float) -> float:\n"
            "    \"\"\"Calculate total invoice cost with tax.\"\"\"\n"
            "    return price + (price * tax)\n\n"
            "print(calculate_total(100.00, 0.05))  # Outputs: 105.0\n"
            "```\n\n"
            "Python supports multiple paradigms (OOP, functional, procedural) and has a massive package ecosystem (PyPI)."
        )
    elif "django" in p_lower:
        return (
            "Django is a model-template-view (MTV) web framework built in Python that follows the 'batteries-included' philosophy.\n\n"
            "### Core MTV Components:\n"
            "1. **Model**: Database schema mapping.\n"
            "2. **Template**: HTML generation and view presentation.\n"
            "3. **View**: Handles requests and responds with rendering layers.\n\n"
            "An example model definition:\n\n"
            "```python\n"
            "from django.db import models\n\n"
            "class Article(models.Model):\n"
            "    title = models.CharField(max_length=200)\n"
            "    body = models.TextField()\n"
            "    pub_date = models.DateTimeField(auto_now_add=True)\n"
            "```"
        )
    elif "sql" in p_lower:
        return (
            "Here is the standard SQL query to retrieve aggregates group-by calculations:\n\n"
            "```sql\n"
            "SELECT \n"
            "    department_id,\n"
            "    COUNT(employee_id) AS total_staff,\n"
            "    AVG(salary) AS average_salary\n"
            "FROM employees\n"
            "WHERE hire_date >= '2023-01-01'\n"
            "GROUP BY department_id\n"
            "HAVING AVG(salary) > 55000\n"
            "ORDER BY average_salary DESC;\n"
            "```"
        )
    elif "email" in p_lower:
        return (
            "### Subject: Request for Project Extension — [Project Name]\n\n"
            "Hi [Manager Name],\n\n"
            "I hope you are doing well.\n\n"
            "I am writing to request a brief timeline extension for the delivery of [Project Name]. "
            "Due to unforeseen dependency blockages on our external API validation pipelines, we require "
            "an additional 3 business days to finish end-to-end regression testing and ensure a premium deployment.\n\n"
            "Our revised delivery target is [New Date]. Let me know if we can sync to review current progress.\n\n"
            "Best regards,\n\n"
            "[Your Name]\n"
            "[Your Role]"
        )
    elif "pdf" in p_lower:
        return (
            "Since the backend mock environment doesn't store active PDFs, I can outline a Python script using PyPDF2 "
            "to extract text contents programmatically:\n\n"
            "```python\n"
            "import PyPDF2\n\n"
            "def extract_pdf_pages(file_path):\n"
            "    with open(file_path, 'rb') as f:\n"
            "        reader = PyPDF2.PdfReader(f)\n"
            "        for idx, page in enumerate(reader.pages):\n"
            "            print(f'--- PAGE {idx+1} ---')\n"
            "            print(page.extract_text())\n"
            "```"
        )
    elif "resume" in p_lower:
        return (
            "Here is a clean resume structure tailored for high-growth tech positions:\n\n"
            "1. **Header**: Name, Title, Contact Info, LinkedIn/GitHub.\n"
            "2. **Summary**: 3-sentence elevator pitch emphasizing technical skills and achievements.\n"
            "3. **Experience**: Reverse-chronological list focusing on quantified outcomes (e.g., 'Optimized query latency by 40%').\n"
            "4. **Projects**: Showcase 2-3 personal/open-source contributions.\n"
            "5. **Education & Certifications**."
        )
    else:
        return (
            f"Hello! I am UMI, your Intelligent AI Assistant. I received your request: \"{prompt}\". "
            "As this is the Django backend demo setup, I've successfully stored this chat in our database."
        )


def get_available_models(request):
    """
    AJAX view returning lists of models depending on the selected provider.
    """
    provider = request.GET.get('provider', 'ollama').strip()
    if provider == 'gemini':
        models = ['gemini-2.5-flash', 'gemini-2.5-pro']
    else:
        models = ai_service.get_ollama_models()
    return JsonResponse({'models': models})


def upload_file(request):
    """
    AJAX view that receives files, validates extension types, 
    saves them in media folder, and registers an Attachment in DB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    upload_start = time.time()
    user = request.user if request.user.is_authenticated else get_dev_user(request)
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        logger.warning(f"UPLOAD | No file provided | User: {user.username}")
        return JsonResponse({'error': 'No file was uploaded'}, status=400)
        
    # Allowed file extensions (including Documents, Images, Markdown, and Code files)
    import os
    allowed_exts = [
        '.pdf', '.docx', '.txt', '.csv', '.xlsx', '.xls', '.pptx',
        '.png', '.jpg', '.jpeg', '.webp',
        '.md', '.markdown', '.py', '.js', '.json', '.html', '.css',
        '.c', '.cpp', '.java', '.go', '.rs', '.sql', '.sh', '.xml', '.yaml', '.yml'
    ]
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if ext not in allowed_exts:
        logger.warning(f"UPLOAD | Unsupported file type: {ext} | File: {uploaded_file.name} | User: {user.username}")
        return JsonResponse({'error': f'File type {ext} is not supported.'}, status=400)
        
    try:
        attachment = Attachment.objects.create(
            user=user,
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=uploaded_file.content_type or 'application/octet-stream'
        )
        upload_duration = round(time.time() - upload_start, 2)
        size_mb = round(uploaded_file.size / (1024 * 1024), 2)
        logger.info(
            f"UPLOAD | File uploaded\n"
            f"  Filename: {uploaded_file.name}\n"
            f"  Size: {size_mb} MB\n"
            f"  Type: {uploaded_file.content_type}\n"
            f"  Duration: {upload_duration}s\n"
            f"  Stored at: {attachment.file.path}\n"
            f"  User: {user.username}"
        )
        return JsonResponse({
            'success': True,
            'id': str(attachment.id),
            'file_name': attachment.file_name,
            'file_size': attachment.file_size,
            'url': attachment.file.url
        })
    except Exception as e:
        logger.error(f"UPLOAD | Failed | File: {uploaded_file.name} | Error: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': f'Failed to upload file: {e}'}, status=500)
