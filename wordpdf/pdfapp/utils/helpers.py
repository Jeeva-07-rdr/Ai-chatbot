"""Shared view helpers."""
import os
import urllib.parse

from django.core.files.storage import FileSystemStorage


UPLOAD_DIR = "media/uploads"


def get_file_storage():
    return FileSystemStorage(location=UPLOAD_DIR)


def make_output(fs, orig_name, new_ext):
    base = os.path.splitext(orig_name)[0]
    out_name = base + new_ext
    out_path = fs.path(out_name)
    return fs.get_available_name(out_path)


def dl_url(stored_path, clean_name):
    return (
        "/download/"
        + urllib.parse.quote(os.path.basename(stored_path))
        + "?name="
        + urllib.parse.quote(clean_name)
    )
