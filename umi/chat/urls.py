from django.urls import path
from . import views

urlpatterns = [
    # Auth URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),

    # Chat URLs
    path('', views.chat_view, name='chat'),
    path('chat/new/', views.new_chat, name='new_chat'),
    path('chat/<uuid:chat_id>/', views.chat_detail_view, name='chat_detail'),
    path('chat/<uuid:chat_id>/send/', views.send_message, name='send_message'),
    path('chat/<uuid:chat_id>/rename/', views.rename_chat, name='rename_chat'),
    path('chat/<uuid:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    path('chat/<uuid:chat_id>/pin/', views.pin_chat, name='pin_chat'),
    path('chat/<uuid:chat_id>/archive/', views.archive_chat, name='archive_chat'),
    path('chat/<uuid:chat_id>/duplicate/', views.duplicate_chat, name='duplicate_chat'),
    path('chat/reorder-pins/', views.reorder_pins, name='reorder_pins'),
    path('chat/search/', views.search_chats, name='search_chats'),
    path('chat/<uuid:chat_id>/export/<str:format_type>/', views.export_chat, name='export_chat'),
    path('chat/upload/', views.upload_file, name='upload_file'),
    
    # Settings & Profile
    path('settings/', views.settings_view, name='settings'),
    path('settings/profile/save/', views.save_profile, name='save_profile'),
    path('settings/profile/avatar/remove/', views.remove_avatar_view, name='remove_avatar'),
    path('settings/preferences/save/', views.save_preferences, name='save_preferences'),
    path('settings/models/', views.get_available_models, name='get_available_models'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    path('settings/clear-history/', views.clear_history, name='clear_history'),
    
    # Help & Notifications
    path('help/', views.help_view, name='help'),
    path('notifications/poll/', views.poll_notifications, name='poll_notifications'),
]
