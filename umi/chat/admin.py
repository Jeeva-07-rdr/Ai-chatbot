from django.contrib import admin
from .models import (
    UserProfile, UserSettings, AIPreferences, Conversation, Message,
    ConversationMemory, Attachment, AuthSession, Analytics, RuntimeLog
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'status', 'created_at')

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'streaming', 'response_style', 'language')

@admin.register(AIPreferences)
class AIPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'model_name', 'temperature', 'max_tokens')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_pinned', 'is_archived', 'is_deleted', 'updated_at')
    list_filter = ('is_pinned', 'is_archived', 'is_deleted')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at')
    list_filter = ('sender',)

@admin.register(ConversationMemory)
class ConversationMemoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'memory_category', 'importance_score', 'created_at')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'file_type', 'file_size', 'created_at')

@admin.register(AuthSession)
class AuthSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ip_address', 'created_at', 'expires_at')

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'request_count', 'avg_response_time', 'error_count')

@admin.register(RuntimeLog)
class RuntimeLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'log_level', 'message')
    list_filter = ('log_level',)
