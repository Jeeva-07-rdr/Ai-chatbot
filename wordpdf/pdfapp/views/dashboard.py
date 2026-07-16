from django.shortcuts import render
from django.http import FileResponse, JsonResponse
import os
import urllib.parse
import logging


from pdfapp.services.editor import (
    prepare_editor_html_from_docx,
    prepare_editor_html_from_pdf,
    html_to_docx_preserving_layout,
)
from pdfapp.services.conversion import (
    safe_docx_to_pdf,
    safe_excel_to_pdf,
    safe_powerpoint_to_pdf,
    safe_powerpoint_to_word,
    safe_pdf_to_powerpoint,
    safe_word_to_powerpoint,
    safe_image_convert,
    merge_excel_files,
    split_excel_file,
)
from pdfapp.services.compression import (
    compress_docx,
    compress_pdf,
    compress_powerpoint,
    compress_image,
    compress_excel,
)
from pdfapp.services.pdf_service import (
    safe_edit_pdf,
    safe_pdf_to_excel,
    safe_image_to_pdf,
)
from pdfapp.services.pdf_to_word import safe_pdf_to_word
from pdfapp.services.exceptions import FileValidationError, public_error_message
from pdfapp.utils.helpers import make_output, dl_url, get_file_storage
from pdfapp.utils.validators import validate_pdf_file

try:
    from htmldocx import HtmlToDocx
except Exception:
    HtmlToDocx = None


logger = logging.getLogger(__name__)


def _remove_file_quietly(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            logger.debug("Could not remove temporary file %s", path, exc_info=True)

def _log_success_to_db(request, action_type, original_name, output_path, download_url, conversion_type=None):
    try:
        from pdfapp.models import ConversionHistory
        
        # 1. Determine conversion type description
        formatted_type = "Conversion"
        if action_type == "word_edit_save":
            formatted_type = "Word Edit"
        elif action_type == "pdf_edit_save" or action_type == "edit_pdf":
            formatted_type = "PDF Edit"
        elif action_type == "merge":
            merge_format = request.POST.get("merge_format", "pdf")
            formatted_type = f"Merge {merge_format.upper()}"
        elif action_type == "split":
            formatted_type = "Split"
        elif action_type == "compress":
            formatted_type = "Compress"
        elif action_type == "convert" and conversion_type:
            type_mapping = {
                "word_to_pdf": "Word to PDF",
                "pdf_to_word": "PDF to Word",
                "excel_to_pdf": "Excel to PDF",
                "pdf_to_excel": "PDF to Excel",
                "image_to_pdf": "Image to PDF",
                "powerpoint_to_pdf": "PowerPoint to PDF",
                "powerpoint_to_word": "PowerPoint to Word",
                "pdf_to_powerpoint": "PDF to PowerPoint",
                "word_to_powerpoint": "Word to PowerPoint",
                "jpeg_to_png": "JPEG to PNG",
                "png_to_jpeg": "PNG to JPEG",
                "image_compress": "Compress Image"
            }
            formatted_type = type_mapping.get(conversion_type, "Conversion")

        # 2. Format file size
        file_size = "Unknown"
        if output_path and os.path.exists(output_path):
            try:
                size_bytes = os.path.getsize(output_path)
                if size_bytes < 1024 * 1024:
                    file_size = f"{size_bytes / 1024:.1f} KB"
                else:
                    file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
            except Exception:
                pass

        # 3. Save to database
        ConversionHistory.objects.create(
            original_filename=original_name,
            converted_filename=os.path.basename(output_path) if output_path else os.path.basename(download_url.split('?')[0]),
            conversion_type=formatted_type,
            file_size=file_size,
            result='Success',
            download_url=download_url,
            record_status='Active',
        )
    except Exception as exc:
        logger.error("Failed to log conversion history: %s", exc, exc_info=True)


def home(request, template_name="dashboard/home.html", active_category="all", active_tool_id=None):

    download_url = None
    error = None

    if request.method == "POST":

        temp_upload_paths = []
        temp_generated_paths = []
        try:
            action_type = request.POST.get("action_type", "convert")
            fs = get_file_storage()

            # Helper: build output path from the user's original filename
            if action_type == "word_edit":
                file_path = None
                try:
                    uploaded_file = request.FILES.get("editwordfile")
                    if not uploaded_file:
                        raise Exception("No Word document uploaded.")
                    original_name = uploaded_file.name
                    filename = fs.save(original_name, uploaded_file)
                    file_path = fs.path(filename)
                    html = prepare_editor_html_from_docx(file_path)
                    return JsonResponse({
                        "success": True,
                        "html": html,
                        "filename": filename,
                        "original_name": original_name
                    })
                except Exception as e:
                    logger.exception("Word edit load failed.")
                    return JsonResponse({
                        "success": False,
                        "error": public_error_message(e)
                    })
                finally:
                    pass

            elif action_type == "pdf_edit_load":
                file_path = None
                try:
                    uploaded_file = request.FILES.get("editfile")
                    if not uploaded_file:
                        raise Exception("No PDF file uploaded.")
                    original_name = uploaded_file.name
                    filename = fs.save(original_name, uploaded_file)
                    file_path = fs.path(filename)
                    temp_upload_paths.append(file_path)
                    html = prepare_editor_html_from_pdf(file_path)
                    return JsonResponse({
                        "success": True,
                        "html": html,
                        "filename": filename,
                        "original_name": original_name
                    })
                except Exception as e:
                    logger.exception("PDF edit load failed.")
                    return JsonResponse({
                        "success": False,
                        "error": public_error_message(e)
                    })
                finally:
                    _remove_file_quietly(file_path)

            elif action_type == "word_edit_save":
                try:
                    html_content = request.POST.get("html_content", "")
                    original_name = request.POST.get("original_name", "document.docx")
                    uploaded_filename = os.path.basename(request.POST.get("uploaded_filename", ""))
                    source_docx = fs.path(uploaded_filename) if uploaded_filename else None
                    
                    base = os.path.splitext(original_name)[0]
                    output_name = base + "_edited.docx"
                    output_path = fs.path(output_name)
                    output_file = fs.get_available_name(output_path)

                    html_to_docx_preserving_layout(html_content, output_file, source_docx)
                    
                    download_url = dl_url(output_file, os.path.basename(output_file))
                    _log_success_to_db(request, action_type, original_name, output_file, download_url)
                    
                    return JsonResponse({
                        "success": True,
                        "download_url": download_url
                    })
                except Exception as e:
                    logger.exception("Word edit save failed.")
                    return JsonResponse({
                        "success": False,
                        "error": public_error_message(e)
                    })
                finally:
                    if "source_docx" in locals():
                        _remove_file_quietly(source_docx)

            elif action_type == "pdf_edit_save":
                docx_tmp = None
                try:
                    html_content = request.POST.get("html_content", "")
                    original_name = request.POST.get("original_name", "document.pdf")

                    base = os.path.splitext(original_name)[0]
                    docx_tmp = fs.get_available_name(fs.path(base + "_edited_temp.docx"))
                    pdf_out = fs.get_available_name(fs.path(base + "_edited.pdf"))

                    html_to_docx_preserving_layout(html_content, docx_tmp)
                    safe_docx_to_pdf(docx_tmp, pdf_out)

                    clean = os.path.basename(pdf_out)
                    download_url = dl_url(pdf_out, clean)
                    _log_success_to_db(request, action_type, original_name, pdf_out, download_url)
                    return JsonResponse({
                        "success": True,
                        "download_url": download_url
                    })
                except Exception as e:
                    logger.exception("PDF edit save failed.")
                    return JsonResponse({
                        "success": False,
                        "error": public_error_message(e)
                    })
                finally:
                    _remove_file_quietly(docx_tmp)

            elif action_type == "convert":
                uploaded_file = request.FILES.get("documentfile")
                if not uploaded_file:
                    raise FileValidationError("Please select a file to convert.")
                conversion_type = request.POST.get(
                    "conversion_type"
                )
                if not conversion_type:
                    raise FileValidationError("Please choose a conversion type.")

                # Capture original name BEFORE Django may rename it
                original_name = uploaded_file.name
                filename = fs.save(original_name, uploaded_file)
                file_path = fs.path(filename)
                temp_upload_paths.append(file_path)
                if conversion_type in ("pdf_to_word", "pdf_to_excel", "pdf_to_powerpoint"):
                    validate_pdf_file(file_path)

                if conversion_type == "word_to_pdf":
                    clean = os.path.splitext(original_name)[0] + ".pdf"
                    output_file = make_output(fs, original_name, ".pdf")
                    safe_docx_to_pdf(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "pdf_to_word":
                    clean = os.path.splitext(original_name)[0] + ".docx"
                    output_file = make_output(fs, original_name, ".docx")
                    safe_pdf_to_word(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "excel_to_pdf":
                    clean = os.path.splitext(original_name)[0] + ".pdf"
                    output_file = make_output(fs, original_name, ".pdf")
                    safe_excel_to_pdf(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "pdf_to_excel":
                    clean = os.path.splitext(original_name)[0] + ".xlsx"
                    output_file = make_output(fs, original_name, ".xlsx")
                    safe_pdf_to_excel(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "image_to_pdf":
                    uploaded_files = request.FILES.getlist("documentfile")
                    if not uploaded_files:
                        raise Exception("Please select at least one image file to convert.")
                    first_orig_name = uploaded_files[0].name
                    temp_paths = []
                    for f in uploaded_files:
                        fn = fs.save(f.name, f)
                        saved_path = fs.path(fn)
                        temp_paths.append(saved_path)
                        temp_upload_paths.append(saved_path)
                    base = os.path.splitext(first_orig_name)[0]
                    clean = base + ".pdf"
                    output_file = fs.get_available_name(fs.path(clean))
                    success = safe_image_to_pdf(temp_paths, output_file)
                    if not success:
                        raise Exception("Image to PDF conversion failed.")
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "powerpoint_to_pdf":
                    clean = os.path.splitext(original_name)[0] + ".pdf"
                    output_file = make_output(fs, original_name, ".pdf")
                    safe_powerpoint_to_pdf(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "powerpoint_to_word":
                    clean = os.path.splitext(original_name)[0] + ".docx"
                    output_file = make_output(fs, original_name, ".docx")
                    safe_powerpoint_to_word(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "pdf_to_powerpoint":
                    clean = os.path.splitext(original_name)[0] + ".pptx"
                    output_file = make_output(fs, original_name, ".pptx")
                    safe_pdf_to_powerpoint(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "word_to_powerpoint":
                    clean = os.path.splitext(original_name)[0] + ".pptx"
                    output_file = make_output(fs, original_name, ".pptx")
                    safe_word_to_powerpoint(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "jpeg_to_png":
                    clean = os.path.splitext(original_name)[0] + ".png"
                    output_file = make_output(fs, original_name, ".png")
                    safe_image_convert(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "png_to_jpeg":
                    clean = os.path.splitext(original_name)[0] + ".jpg"
                    output_file = make_output(fs, original_name, ".jpg")
                    safe_image_convert(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "image_compress":
                    orig_ext = os.path.splitext(original_name)[1].lower()
                    base = os.path.splitext(original_name)[0]
                    clean = original_name
                    out_name = base + "_compressed" + orig_ext
                    output_file = fs.get_available_name(fs.path(out_name))
                    success = compress_image(file_path, output_file)
                    if not success:
                        raise Exception("Image compression failed.")
                    download_url = dl_url(output_file, clean)

                _log_success_to_db(request, action_type, original_name, output_file, download_url, conversion_type)

            elif action_type == "edit_pdf":
                uploaded_file = request.FILES.get("editfile")
                if not uploaded_file:
                    raise Exception("Please select a PDF file to edit.")
                original_name = uploaded_file.name
                filename = fs.save(original_name, uploaded_file)
                file_path = fs.path(filename)
                temp_upload_paths.append(file_path)
                base = os.path.splitext(original_name)[0]
                output_file = fs.get_available_name(fs.path(base + "_edited.pdf"))
                safe_edit_pdf(file_path, output_file, request.POST.get("pdf_edit_actions", "[]"))
                download_url = dl_url(output_file, original_name)
                _log_success_to_db(request, action_type, original_name, output_file, download_url)

            elif action_type == "merge":
                merge_files = request.FILES.getlist("mergefiles")
                merge_format = request.POST.get("merge_format", "pdf")

                if not merge_files or len(merge_files) < 2:
                    raise Exception("Please select at least 2 files to merge.")


                # Capture original names BEFORE saving
                merge_orig_names = [f.name for f in merge_files]
                temp_paths = []
                for f in merge_files:
                    fn = fs.save(f.name, f)
                    saved_path = fs.path(fn)
                    temp_paths.append(saved_path)
                    temp_upload_paths.append(saved_path)

                def make_merged_name(orig_names, ext):
                    base = os.path.splitext(orig_names[0])[0]
                    out_name = base + ext
                    return fs.get_available_name(fs.path(out_name))

                if merge_format == "pdf":
                    import fitz
                    merged_doc = fitz.open()
                    for path in temp_paths:
                        validate_pdf_file(path)
                        sub_doc = fitz.open(path)
                        merged_doc.insert_pdf(sub_doc)
                    clean = os.path.splitext(merge_orig_names[0])[0] + ".pdf"
                    output_path = make_merged_name(merge_orig_names, ".pdf")
                    merged_doc.save(output_path)
                    merged_doc.close()
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_path)) + "?name=" + urllib.parse.quote(clean)

                elif merge_format == "docx":
                    import docx
                    from docxcompose.composer import Composer
                    master = docx.Document(temp_paths[0])
                    composer = Composer(master)
                    for path in temp_paths[1:]:
                        doc_temp = docx.Document(path)
                        master.add_page_break()
                        composer.append(doc_temp)
                    clean = os.path.splitext(merge_orig_names[0])[0] + ".docx"
                    output_path = make_merged_name(merge_orig_names, ".docx")
                    composer.save(output_path)
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_path)) + "?name=" + urllib.parse.quote(clean)

                elif merge_format == "xlsx":
                    clean = os.path.splitext(merge_orig_names[0])[0] + ".xlsx"
                    output_path = make_merged_name(merge_orig_names, ".xlsx")
                    success = merge_excel_files(temp_paths, output_path)
                    if not success:
                        raise Exception("Excel merging failed.")
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_path)) + "?name=" + urllib.parse.quote(clean)

                _log_success_to_db(request, action_type, merge_orig_names[0] if merge_orig_names else "Merged Files", output_path, download_url)

            elif action_type == "split":
                uploaded_files = request.FILES.getlist("splitfile")
                page_range_str = request.POST.get("page_range", "all").strip()

                if not uploaded_files:
                    raise Exception("Please select at least one file to split.")

                # Capture original names BEFORE saving
                split_orig_names = [f.name for f in uploaded_files]
                temp_paths = []
                for f in uploaded_files:
                    fn = fs.save(f.name, f)
                    saved_path = fs.path(fn)
                    temp_paths.append(saved_path)
                    temp_upload_paths.append(saved_path)

                def parse_page_ranges_to_groups(range_str, max_pages):
                    if not range_str or range_str.lower() == "all":
                        return [(f"page_{p+1}", [p]) for p in range(max_pages)]
                    groups = []
                    parts = range_str.split(",")
                    for part in parts:
                        part = part.strip().lower()
                        if not part:
                            continue
                        if part == "odd":
                            pages = [p for p in range(max_pages) if p % 2 == 0]
                            if pages:
                                groups.append(("odd_pages", pages))
                        elif part == "even":
                            pages = [p for p in range(max_pages) if p % 2 != 0]
                            if pages:
                                groups.append(("even_pages", pages))
                        elif "-" in part:
                            try:
                                start, end = part.split("-")
                                s = int(start.strip()) - 1
                                e = int(end.strip()) - 1
                                pages = [p for p in range(s, e + 1) if 0 <= p < max_pages]
                                if pages:
                                    groups.append((f"pages_{start.strip()}-{end.strip()}", pages))
                            except ValueError:
                                pass
                        else:
                            try:
                                p_num = int(part)
                                p = p_num - 1
                                if 0 <= p < max_pages:
                                    groups.append((f"page_{p_num}", [p]))
                            except ValueError:
                                pass
                    return groups

                output_paths = []

                for idx, file_path in enumerate(temp_paths):
                    # Use original uploaded name for output naming
                    orig_name = split_orig_names[idx] if idx < len(split_orig_names) else os.path.basename(file_path)
                    is_pdf = file_path.lower().endswith(".pdf")
                    is_docx = file_path.lower().endswith(".docx")
                    is_xlsx = file_path.lower().endswith(".xlsx") or file_path.lower().endswith(".xls")

                    if not is_pdf and not is_docx and not is_xlsx:
                        continue

                    if is_pdf:
                        validate_pdf_file(file_path)
                        import fitz
                        doc = fitz.open(file_path)
                        groups = parse_page_ranges_to_groups(page_range_str, len(doc))
                        if not groups:
                            doc.close()
                            raise Exception(f"Invalid page range specified for {orig_name}.")
                        
                        for group_name, pages in groups:
                            sub_doc = fitz.open(file_path)
                            sub_doc.select(pages)
                            base, ext = os.path.splitext(orig_name)
                            output_filename = f"{base}_{group_name}{ext}"
                            output_path = fs.path(output_filename)
                            output_path = fs.get_available_name(output_path)
                            sub_doc.save(output_path)
                            sub_doc.close()
                            output_paths.append(output_path)
                        doc.close()

                    elif is_docx:
                        temp_pdf_path = os.path.splitext(file_path)[0] + "_temp.pdf"
                        temp_generated_paths.append(temp_pdf_path)
                        safe_docx_to_pdf(file_path, temp_pdf_path)

                        import fitz
                        doc = fitz.open(temp_pdf_path)
                        groups = parse_page_ranges_to_groups(page_range_str, len(doc))
                        doc.close()

                        if not groups:
                            os.remove(temp_pdf_path)
                            raise Exception(f"Invalid page range specified for {orig_name}.")

                        for group_name, pages in groups:
                            pdf_doc = fitz.open(temp_pdf_path)
                            pdf_doc.select(pages)
                            split_pdf_path = os.path.splitext(file_path)[0] + f"_{group_name}_split_temp.pdf"
                            temp_generated_paths.append(split_pdf_path)
                            pdf_doc.save(split_pdf_path)
                            pdf_doc.close()

                            base, ext = os.path.splitext(orig_name)
                            output_filename = f"{base}_{group_name}{ext}"
                            output_path = fs.path(output_filename)
                            output_path = fs.get_available_name(output_path)

                            safe_pdf_to_word(split_pdf_path, output_path)

                            os.remove(split_pdf_path)
                            output_paths.append(output_path)

                        os.remove(temp_pdf_path)

                    elif is_xlsx:
                        excel_outputs = split_excel_file(file_path, page_range_str, fs)
                        output_paths.extend(excel_outputs)

                if not output_paths:
                    raise Exception("No files were successfully split.")

                if len(output_paths) == 1:
                    # Single split file: serve with clean name (no random suffix)
                    base, ext = os.path.splitext(os.path.basename(output_paths[0]))
                    # Strip any Django random suffix — use the stored name as-is from our output_filename var
                    clean_split = split_orig_names[0] if split_orig_names else os.path.basename(output_paths[0])
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_paths[0])) + "?name=" + urllib.parse.quote(clean_split)
                else:
                    import zipfile
                    if len(split_orig_names) == 1:
                        base = os.path.splitext(split_orig_names[0])[0]
                        zip_clean = os.path.splitext(split_orig_names[0])[0] + ".zip"
                    else:
                        zip_clean = "split_results.zip"
                    zip_path = fs.get_available_name(fs.path(zip_clean))
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for path in output_paths:
                            zipf.write(path, os.path.basename(path))
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(zip_path)) + "?name=" + urllib.parse.quote(zip_clean)

                split_out_path = output_paths[0] if len(output_paths) == 1 else zip_path
                _log_success_to_db(request, action_type, split_orig_names[0] if split_orig_names else "Split File", split_out_path, download_url)

            elif action_type == "compress":
                uploaded_files = request.FILES.getlist("compressfiles")
                if not uploaded_files:
                    raise Exception("Please select at least one file to compress.")

                # Capture original names BEFORE saving
                compress_orig_names = [f.name for f in uploaded_files]
                temp_paths = []
                for f in uploaded_files:
                    fn = fs.save(f.name, f)
                    saved_path = fs.path(fn)
                    temp_paths.append(saved_path)
                    temp_upload_paths.append(saved_path)

                output_paths = []
                for cidx, file_path in enumerate(temp_paths):
                    orig_name = compress_orig_names[cidx] if cidx < len(compress_orig_names) else os.path.basename(file_path)
                    is_pdf = file_path.lower().endswith(".pdf")
                    is_docx = file_path.lower().endswith(".docx")
                    is_xlsx = file_path.lower().endswith(".xlsx") or file_path.lower().endswith(".xls")
                    is_pptx = file_path.lower().endswith(".pptx") or file_path.lower().endswith(".ppt")

                    if not is_pdf and not is_docx and not is_xlsx and not is_pptx:
                        continue

                    base, ext = os.path.splitext(orig_name)
                    output_filename = base + "_compressed" + ext
                    output_path = fs.get_available_name(fs.path(output_filename))

                    success = False
                    if is_pdf:
                        validate_pdf_file(file_path)
                        success = compress_pdf(file_path, output_path)
                    elif is_docx:
                        success = compress_docx(file_path, output_path)
                    elif is_xlsx:
                        success = compress_excel(file_path, output_path)
                    elif is_pptx:
                        success = compress_powerpoint(file_path, output_path)

                    if success:
                        output_paths.append(output_path)

                if not output_paths:
                    raise Exception("No files were successfully compressed.")

                if len(output_paths) == 1:
                    orig_name_0 = compress_orig_names[0] if compress_orig_names else os.path.basename(output_paths[0])
                    base0, ext0 = os.path.splitext(orig_name_0)
                    clean_c = orig_name_0
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_paths[0])) + "?name=" + urllib.parse.quote(clean_c)
                else:
                    import zipfile
                    if len(compress_orig_names) == 1:
                        base = os.path.splitext(compress_orig_names[0])[0]
                        zip_clean = os.path.splitext(compress_orig_names[0])[0] + ".zip"
                    else:
                        zip_clean = "compressed_results.zip"
                    zip_path = fs.get_available_name(fs.path(zip_clean))
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for path in output_paths:
                            zipf.write(path, os.path.basename(path))
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(zip_path)) + "?name=" + urllib.parse.quote(zip_clean)

                compress_out_path = output_paths[0] if len(output_paths) == 1 else zip_path
                _log_success_to_db(request, action_type, compress_orig_names[0] if compress_orig_names else "Compressed File", compress_out_path, download_url)

        except Exception as e:
            logger.exception("Document operation failed.")
            error = public_error_message(e)
        finally:
            for path in temp_generated_paths + temp_upload_paths:
                _remove_file_quietly(path)

    return render(
        request,
        template_name,
        {
            "download_url": download_url,
            "error": error,
            "active_category": active_category,
            "active_tool_id": active_tool_id,
        }
    )
def download_file(request, filename):
    file_path = os.path.join(
        "media",
        "uploads",
        filename
    )
    # Use the ?name= query param as the browser-facing filename if provided
    display_name = request.GET.get("name", filename)
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=display_name
    )


def tool_page(request, template_name, active_category, active_tool_id=None):
    """Render a category or tool page; POST handling is identical to the home dashboard."""
    return home(
        request,
        template_name=template_name,
        active_category=active_category,
        active_tool_id=active_tool_id,
    )


def get_history(request):
    """Retrieve latest 20 Active conversion history records as JSON."""
    from pdfapp.models import ConversionHistory
    history = ConversionHistory.objects.filter(record_status='Active').order_by('-created_at')[:20]
    data = []
    for item in history:
        data.append({
            'id': item.id,
            'original_filename': item.original_filename,
            'converted_filename': item.converted_filename,
            'conversion_type': item.conversion_type,
            'file_size': item.file_size,
            'result': item.result,
            'download_url': item.download_url,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': item.record_status,
        })
    return JsonResponse({'success': True, 'history': data})


def delete_history_item(request, item_id):
    """Soft-delete a single conversion history record (marks it Inactive)."""
    from pdfapp.models import ConversionHistory
    if request.method in ('POST', 'DELETE'):
        try:
            item = ConversionHistory.objects.get(id=item_id)
            item.soft_delete()
            return JsonResponse({'success': True})
        except ConversionHistory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def restore_history_item(request, item_id):
    """Restore a single Inactive conversion history record back to Active."""
    from pdfapp.models import ConversionHistory
    if request.method == 'POST':
        try:
            item = ConversionHistory.objects.get(id=item_id)
            item.restore()
            return JsonResponse({'success': True})
        except ConversionHistory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def clear_history(request):
    """Soft-clear: marks all Active records as Inactive. No rows are deleted."""
    from pdfapp.models import ConversionHistory
    if request.method == 'POST':
        ConversionHistory.objects.filter(record_status='Active').update(record_status='Inactive')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
