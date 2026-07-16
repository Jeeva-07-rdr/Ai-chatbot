from django.urls import include, path

urlpatterns = [
    path("", include("pdfapp.urls.dashboard_urls")),
    path("pdf/", include("pdfapp.urls.pdf_urls")),
    path("word/", include("pdfapp.urls.word_urls")),
    path("excel/", include("pdfapp.urls.excel_urls")),
    path("powerpoint/", include("pdfapp.urls.powerpoint_urls")),
    path("image/", include("pdfapp.urls.image_urls")),
]
