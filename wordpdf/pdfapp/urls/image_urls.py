from django.urls import path

from pdfapp.views import image_views

urlpatterns = [
    path("", image_views.image_dashboard, name="image_dashboard"),
    path("jpeg-to-png/", image_views.jpeg_to_png, name="jpeg_to_png"),
    path("png-to-jpeg/", image_views.png_to_jpeg, name="png_to_jpeg"),
    path("image-compress/", image_views.image_compress, name="image_compress"),
]
