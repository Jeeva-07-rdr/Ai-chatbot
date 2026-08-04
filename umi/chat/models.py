import uuid
from django.db import models
from django.contrib.auth.models import User

# Point built-in User model to 'users' table
User._meta.db_table = 'users'

# Point built-in LogEntry model to 'runtime_logs' table
from django.contrib.admin.models import LogEntry
LogEntry._meta.db_table = 'runtime_logs'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=50, default='user')
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile for {self.user.username}"


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
    STYLE_CHOICES = [
        ('short', 'Short'),
        ('balanced', 'Balanced'),
        ('detailed', 'Detailed'),
        ('research', 'Research'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    ai_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='ollama')
    ai_model = models.CharField(max_length=100, default='qwen2.5:0.5b')
    streaming = models.BooleanField(default=True)
    response_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='balanced')
    language = models.CharField(max_length=10, default='en')
    notifications = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_settings'

    def __str__(self):
        return f"Settings for {self.user.username}"


class AIPreferences(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_preferences')
    provider = models.CharField(max_length=50, default='ollama')
    model_name = models.CharField(max_length=100, default='qwen2.5:0.5b')
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_preferences'

    def __str__(self):
        return f"AI Preferences ({self.provider}/{self.model_name}) for {self.user.username}"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default='New Chat')
    
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.id})"





class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', db_column='session_id')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    content = models.TextField()
    tokens_used = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender} in {self.conversation.title}"


class ConversationMemory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True, related_name='memories', db_column='session_id')
    memory_category = models.CharField(max_length=50, default='general')
    memory_content = models.TextField()
    importance_score = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation_memory'
        ordering = ['-importance_score', '-created_at']

    def __str__(self):
        return f"Memory ({self.memory_category}): {self.memory_content[:30]}..."


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents', db_column='session_id')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True, db_column='message_id')
    file = models.FileField(upload_to='attachments/', null=True, blank=True, db_column='file_path')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()
    processing_status = models.CharField(max_length=20, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents'

    def __str__(self):
        return f"{self.file_name} ({self.file_size} bytes)"


class AuthSession(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_sessions', null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'auth_sessions'


class Analytics(models.Model):
    request_count = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    token_usage = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Analytics @ {self.timestamp} - Req: {self.request_count}"


class RuntimeLog(models.Model):
    log_level = models.CharField(max_length=20, default='INFO')
    message = models.TextField()
    exception = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'runtime_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.log_level}] {self.message[:30]}..."


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens', db_column='user_id')
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()

    @classmethod
    def clean_expired_tokens(cls):
        from django.utils import timezone
        cls.objects.filter(expires_at__lt=timezone.now()).delete()

    def __str__(self):
        return f"ResetToken for {self.user.username} (Used: {self.is_used})"

