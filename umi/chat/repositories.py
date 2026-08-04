import logging
from django.db import transaction
from django.contrib.auth.models import User
from chat.models import (
    UserProfile, UserSettings, AIPreferences, Conversation, Message,
    ConversationMemory, Attachment, AuthSession, Analytics, RuntimeLog
)

logger = logging.getLogger('umi')

class UserRepository:
    """Repository handling User accounts, profiles, and settings persistence."""
    
    @staticmethod
    def get_or_create_settings(user):
        """Get or initialize UserSettings and AIPreferences for a given user."""
        settings, _ = UserSettings.objects.get_or_create(user=user)
        AIPreferences.objects.get_or_create(user=user)
        UserProfile.objects.get_or_create(user=user)
        return settings

    @staticmethod
    def update_settings(user, **kwargs):
        """Update UserSettings and AIPreferences with validation and transaction safety."""
        with transaction.atomic():
            settings, _ = UserSettings.objects.get_or_create(user=user)
            ai_pref, _ = AIPreferences.objects.get_or_create(user=user)
            
            if 'ai_provider' in kwargs:
                ai_pref.provider = kwargs.pop('ai_provider')
            if 'ai_model' in kwargs:
                ai_pref.model_name = kwargs.pop('ai_model')
            ai_pref.save()

            for key, val in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, val)
            settings.save()
            return settings


class ChatRepository:
    """Repository handling ChatGPT-style session CRUD, messages, and long-term memory."""

    @staticmethod
    def create_session(user, title='New Chat'):
        """Create a new chat session."""
        session = Conversation.objects.create(user=user, title=title)
        logger.info(f"CHAT_REPO | Session created | ID: {session.id} | User: {user.username}")
        return session

    @staticmethod
    def get_user_sessions(user):
        """Get all active, non-deleted chat sessions for a user."""
        return Conversation.objects.filter(user=user, is_deleted=False).order_by('-updated_at')

    @staticmethod
    def get_session_by_id(user, session_id):
        """Retrieve a specific chat session by UUID."""
        try:
            return Conversation.objects.get(id=session_id, user=user, is_deleted=False)
        except Conversation.DoesNotExist:
            return None

    @staticmethod
    def add_message(session, sender, content, tokens_used=0, processing_time_ms=0):
        """Add a message to a session and touch last_activity timestamp."""
        with transaction.atomic():
            msg = Message.objects.create(
                conversation=session,
                sender=sender,
                content=content,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms
            )
            session.save() # Touch updated_at and last_activity
            return msg

    @staticmethod
    def soft_delete_session(user, session_id):
        """Soft delete a chat session."""
        session = ChatRepository.get_session_by_id(user, session_id)
        if session:
            session.is_deleted = True
            session.save()
            logger.info(f"CHAT_REPO | Session soft deleted | ID: {session_id}")
            return True
        return False

    @staticmethod
    def rename_session(user, session_id, new_title):
        """Rename a chat session title."""
        session = ChatRepository.get_session_by_id(user, session_id)
        if session:
            session.title = new_title[:255]
            session.save()
            return session
        return None

    @staticmethod
    def toggle_pin(user, session_id):
        """Toggle pinned status for a session."""
        session = ChatRepository.get_session_by_id(user, session_id)
        if session:
            session.is_pinned = not session.is_pinned
            session.save()
            return session.is_pinned
        return False

    @staticmethod
    def add_memory(user, session, content, category='general', importance_score=1.0):
        """Store long-term AI memory."""
        return ConversationMemory.objects.create(
            user=user,
            conversation=session,
            memory_category=category,
            memory_content=content,
            importance_score=importance_score
        )

    @staticmethod
    def get_memories(user, limit=5):
        """Fetch top relevant long-term memories for a user."""
        return ConversationMemory.objects.filter(user=user).order_by('-importance_score', '-created_at')[:limit]


class AnalyticsRepository:
    """Repository handling runtime analytics and logs."""

    @staticmethod
    def log_runtime(level, message, exception=None):
        """Audit trail for runtime execution logs."""
        try:
            return RuntimeLog.objects.create(
                log_level=level,
                message=message,
                exception=exception
            )
        except Exception as e:
            logger.warning(f"ANALYTICS_REPO | Failed to log runtime: {e}")
            return None
