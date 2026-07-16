from django.urls import path

from pdfapp.views.dashboard import home, download_file, get_history, delete_history_item, clear_history, restore_history_item

urlpatterns = [
    path("", home, name="home"),
    path("download/<str:filename>", download_file, name="download_file"),
    path("history/", get_history, name="get_history"),
    path("history/delete/<int:item_id>/", delete_history_item, name="delete_history_item"),
    path("history/clear/", clear_history, name="clear_history"),
    path("history/restore/<int:item_id>/", restore_history_item, name="restore_history_item"),
]

