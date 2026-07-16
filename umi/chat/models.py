import uuid
from django.db import models
from django.contrib.auth.models import User

class UserSettings(models.Model):
    THEME_CHOICES = [
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('system', 'System Theme'),
    ]
    
    PROVIDER_CHOICES = [
        ('gemini', 'Gemini'),
        ('ollama', 'Ollama'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    
    # Profile information (fallback to auth.User fields, but custom picture)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # AI Settings
    ai_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='ollama')
    ai_model = models.CharField(max_length=100, default='qwen2.5:0.5b')
    streaming = models.BooleanField(default=True)
    
    STYLE_CHOICES = [
        ('short', 'Short'),
        ('balanced', 'Balanced'),
        ('detailed', 'Detailed'),
        ('research', 'Research'),
    ]
    response_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='balanced')

    def __str__(self):
        return f"Settings for {self.user.username}"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default='New Chat')
    
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.id})"


class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=5, choices=SENDER_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender} in {self.conversation.title}"


class PinnedConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_items')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='pinned_relationship')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']
        unique_together = ('user', 'conversation')

    def __str__(self):
        return f"Pin: {self.conversation.title} (Order: {self.sort_order})"


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    file = models.FileField(upload_to='attachments/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} ({self.file_size} bytes)"
