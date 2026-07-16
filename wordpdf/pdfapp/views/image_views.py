from .dashboard import tool_page


def image_dashboard(request):
    return tool_page(request, "image/dashboard.html", "image")


def jpeg_to_png(request):
    return tool_page(request, "image/jpeg_to_png.html", "image", "jpeg-to-png")


def png_to_jpeg(request):
    return tool_page(request, "image/png_to_jpeg.html", "image", "png-to-jpeg")


def image_compress(request):
    return tool_page(request, "image/image_compress.html", "image", "image-compress")
