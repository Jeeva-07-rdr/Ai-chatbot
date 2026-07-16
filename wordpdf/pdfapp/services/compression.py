import os

def compress_docx(input_path, output_path, image_quality=70, max_width=1200):
    try:
        import zipfile
        import io
        from PIL import Image
        
        with zipfile.ZipFile(input_path, 'r') as yin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename.startswith("word/media/") and any(item.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(float(img.height) * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                            
                            out_bytes = io.BytesIO()
                            img_format = img.format if img.format else "JPEG"
                            if img_format == "PNG" and img.mode in ('RGBA', 'LA'):
                                img.save(out_bytes, format="PNG", optimize=True)
                            else:
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.save(out_bytes, format="JPEG", quality=image_quality, optimize=True)
                                
                            compressed_data = out_bytes.getvalue()
                            if len(compressed_data) < len(data):
                                data = compressed_data
                        except Exception as img_err:
                            print(f"Failed to compress image {item.filename}: {img_err}")
                    yout.writestr(item, data)
        return True
    except Exception as e:
        print(f"Error compressing docx: {e}")
        return False

def compress_pdf(input_path, output_path):
    try:
        import fitz
        doc = fitz.open(input_path)
        doc.scrub(
            metadata=True,
            xml_metadata=True,
            attached_files=True,
            embedded_files=True,
            thumbnails=True,
            reset_fields=False,
            reset_responses=False
        )
        doc.ez_save(
            output_path,
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            use_objstms=True
        )
        doc.close()
        return True
    except Exception as e:
        print(f"Error compressing pdf: {e}")
        return False

def compress_powerpoint(input_path, output_path, image_quality=70, max_width=1200):
    try:
        import zipfile
        import io
        from PIL import Image
        
        with zipfile.ZipFile(input_path, 'r') as yin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename.startswith("ppt/media/") and any(item.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(float(img.height) * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                            
                            out_bytes = io.BytesIO()
                            img_format = img.format if img.format else "JPEG"
                            if img_format == "PNG" and img.mode in ('RGBA', 'LA'):
                                img.save(out_bytes, format="PNG", optimize=True)
                            else:
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.save(out_bytes, format="JPEG", quality=image_quality, optimize=True)
                                
                            compressed_data = out_bytes.getvalue()
                            if len(compressed_data) < len(data):
                                data = compressed_data
                        except Exception as img_err:
                            print(f"Failed to compress presentation image {item.filename}: {img_err}")
                    yout.writestr(item, data)
        return True
    except Exception as e:
        print(f"Error compressing powerpoint: {e}")
        return False

def compress_image(input_path, output_path, quality=70, max_width=1920):
    try:
        from PIL import Image
        img = Image.open(input_path)
        # Resize if wider than max_width
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        # Determine output format from extension
        ext = os.path.splitext(output_path)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
        elif ext == '.png':
            img.save(output_path, format='PNG', optimize=True)
        else:
            img.save(output_path, optimize=True)
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def compress_excel(input_path, output_path, image_quality=70, max_width=1200):
    try:
        import zipfile
        import io
        from PIL import Image
        
        with zipfile.ZipFile(input_path, 'r') as yin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename.startswith("xl/media/") and any(item.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(float(img.height) * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                            
                            out_bytes = io.BytesIO()
                            img_format = img.format if img.format else "JPEG"
                            if img_format == "PNG" and img.mode in ('RGBA', 'LA'):
                                img.save(out_bytes, format="PNG", optimize=True)
                            else:
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.save(out_bytes, format="JPEG", quality=image_quality, optimize=True)
                                
                            compressed_data = out_bytes.getvalue()
                            if len(compressed_data) < len(data):
                                data = compressed_data
                        except Exception as img_err:
                            print(f"Failed to compress Excel image {item.filename}: {img_err}")
                    yout.writestr(item, data)
        return True
    except Exception as e:
        print(f"Error compressing excel: {e}")
        return False

