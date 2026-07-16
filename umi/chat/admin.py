from django.contrib import admin
from .models import UserSettings, Conversation, Message, PinnedConversation

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'ai_provider', 'ai_model', 'streaming')
    search_fields = ('user__username', 'ai_model')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_pinned', 'is_archived', 'is_deleted', 'created_at', 'updated_at')
    list_filter = ('is_pinned', 'is_archived', 'is_deleted', 'created_at')
    search_fields = ('title', 'user__username', 'id')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at')
    list_filter = ('sender', 'created_at')
    search_fields = ('content', 'conversation__title')

@admin.register(PinnedConversation)
class PinnedConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'conversation', 'sort_order')
    list_filter = ('user',)
    ordering = ('sort_order',)
