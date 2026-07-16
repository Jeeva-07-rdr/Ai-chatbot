import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set cell background color."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding for table cells in twentieths of a point (dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_heading_with_color(doc, text, level, rgb_color):
    """Add a heading and set its color and font."""
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    for r in h.runs:
        r.font.name = 'Segoe UI'
        r.font.color.rgb = rgb_color
    return h

def create_report():
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles Setup
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Segoe UI'
    style_normal.font.size = Pt(10.5)
    style_normal.font.color.rgb = RGBColor(51, 51, 51)
    
    COLOR_PRIMARY = RGBColor(26, 82, 118)   # Deep Blue
    COLOR_SECONDARY = RGBColor(93, 109, 126) # Muted Slate
    COLOR_HIGHLIGHT = RGBColor(220, 118, 51) # Accent Orange
    
    # ------------------ COVER PAGE ------------------
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(120)
    title_run = title_p.add_run("DocuConverter Pro")
    title_run.font.size = Pt(36)
    title_run.font.bold = True
    title_run.font.color.rgb = COLOR_PRIMARY
    
    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(200)
    sub_run = sub_p.add_run("Package Reference & System Installation Guide")
    sub_run.font.size = Pt(16)
    sub_run.font.color.rgb = COLOR_SECONDARY
    
    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta_p.add_run("System Documentation & Reference Handbook\nGenerated: June 30, 2026\nVersion 1.0")
    meta_run.font.size = Pt(10)
    meta_run.font.color.rgb = COLOR_SECONDARY
    
    doc.add_page_break()
    
    # ------------------ TABLE OF CONTENTS / INTRO ------------------
    add_heading_with_color(doc, "1. Executive Summary & Architecture", 1, COLOR_PRIMARY)
    
    intro_p = doc.add_paragraph(
        "DocuConverter Pro is an instant file utility web application designed to convert, merge, split, compress, "
        "and edit files across formats including Word (DOC/DOCX), PDF, Excel (XLS/XLSX), PowerPoint (PPT/PPTX), "
        "and Images (PNG/JPEG). The platform is built using Python, Django, and a suite of high-fidelity "
        "document-manipulation packages. It runs an automated system of fallback engines—specifically leveraging "
        "local Microsoft Word and PowerPoint COM automation interfaces on Windows servers to maintain exact font, layout, "
        "and pagination fidelity, while falling back to cross-platform open-source alternatives where required."
    )
    intro_p.paragraph_format.space_after = Pt(12)
    intro_p.paragraph_format.line_spacing = 1.15
    
    # ------------------ SECTION 2: PYTHON PACKAGES ------------------
    add_heading_with_color(doc, "2. Python Package Directory", 1, COLOR_PRIMARY)
    
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    # Format Table Header
    hdr_cells = table.rows[0].cells
    headers = ["Package Name", "Primary Purpose", "Core System Functionality"]
    widths = [Inches(1.8), Inches(1.8), Inches(2.9)]
    
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        hdr_cells[i].width = widths[i]
        set_cell_background(hdr_cells[i], "1A5276")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=150, right=150)
        # Apply bold white font to headers
        for p in hdr_cells[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.size = Pt(10)

    # Package list
    packages = [
        ("Django (6.0.6)", 
         "Core Web MVC Framework", 
         "Manages settings.py, URL routing, requests/views, CSRF security, model databases (db.sqlite3), session storage, templates, and dashboard file uploads."),
        
        ("PyMuPDF / fitz (1.27.2)", 
         "PDF Processing & Page Rendering", 
         "Retrieves PDF metadata/page counts, extracts raw text, highlights text strings, performs search-and-replace on text streams, and compresses PDFs via image extract/downsample."),
         
        ("python-docx (1.2.0)", 
         "Word DOCX Layout & Construction", 
         "Parses and manipulates Word files. Performs DOCX inspection (counting paragraphs, tables, words) and structures document styles programmatically."),
         
        ("docxcompose (2.2.0)", 
         "DOCX Style-Preserving Merging", 
         "Safely combines multiple DOCX documents into a single output without losing original margins, page headers, footers, image layouts, or numbering definitions."),
         
        ("mammoth (1.12.0)", 
         "DOCX to HTML Conversion", 
         "Converts uploaded Word (.docx) documents into clean, semantic HTML format for rendering directly in the browser's Word Editor visual workspace."),
         
        ("htmldocx (0.0.6)", 
         "HTML to DOCX Exporting", 
         "Converts HTML text markup from the browser's Word Editor canvas back into native DOCX files when the user clicks 'Save Changes'."),
         
        ("pdf2docx (0.5.13)", 
         "PDF to Word Conversion Engine", 
         "Reconstructs document layout structure from PDF pages—converting lines, paragraphs, grids, and tables into editable DOCX document components."),
         
        ("pdfplumber (0.11.10)", 
         "PDF Layout Table Parsing", 
         "Parses precise grid coordinates of tables inside PDFs to extract raw cell data, structures it, and prepares it for export to Excel formats."),
         
        ("openpyxl (3.1.5)", 
         "Excel XLS/XLSX Engine", 
         "Writes structured tabular data extracted from PDFs into formatted spreadsheet grids, supporting sheet creation, formulas, and style settings."),
         
        ("pywin32 / win32com (312)", 
         "Windows COM Automation Bridge", 
         "Bridges Python to Windows COM APIs, allowing background automation of Microsoft Word and PowerPoint desktop applications for high-fidelity conversion."),
         
        ("Pillow / PIL (12.2.0)", 
         "Image Processing Framework", 
         "Used in image and compression tools to crop, resize, convert formats, and scale image quality for PDF size reduction workflows.")
    ]
    
    # Populating Table
    for row_idx, (name, purpose, usage) in enumerate(packages):
        row = table.add_row()
        cells = row.cells
        
        cells[0].text = name
        cells[1].text = purpose
        cells[2].text = usage
        
        # Alternating background colors
        bg_hex = "F4F6F7" if row_idx % 2 == 1 else "FFFFFF"
        
        for col_idx in range(3):
            cells[col_idx].width = widths[col_idx]
            set_cell_background(cells[col_idx], bg_hex)
            set_cell_margins(cells[col_idx], top=100, bottom=100, left=150, right=150)
            for p in cells[col_idx].paragraphs:
                p.paragraph_format.line_spacing = 1.05
                for r in p.runs:
                    r.font.size = Pt(9.5)
                    if col_idx == 0:
                        r.font.bold = True
                        r.font.color.rgb = COLOR_PRIMARY
                        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    doc.add_page_break()

    # ------------------ SECTION 3: FUNCTION MAP ------------------
    add_heading_with_color(doc, "3. Function-Level Dependency Mapping", 1, COLOR_PRIMARY)
    
    mapping_p = doc.add_paragraph("This section outlines exactly where and how these third-party packages are imported and used within specific Python scripts and view handlers:")
    mapping_p.paragraph_format.space_after = Pt(12)
    
    functions = [
        ("Word Editor Import (`word_edit`)", 
         "File: pdfapp/views.py", 
         "Uses `mammoth` to convert uploaded docx files to clean HTML strings. The converted HTML is returned as a JSON response to the front-end A4 visual canvas."),
        
        ("Word Editor Export (`word_edit_save`)", 
         "File: pdfapp/views.py", 
         "Uses `htmldocx.HtmlToDocx` to convert edited HTML strings back into standard DOCX binary format for downloading and filesystem persistence."),
         
        ("Word to PDF Conversion (`safe_docx_to_pdf`)", 
         "File: pdfapp/services/word_to_pdf.py & word_com.py", 
         "Uses `win32com.client.DispatchEx('Word.Application')` to start a headless Microsoft Word background process. Word opens the document and invokes `ExportAsFixedFormat` to output an exact PDF replica."),
         
        ("PDF to Word Conversion (`pdf_to_word_service`)", 
         "File: pdfapp/services/pdf_to_word.py & word_com.py", 
         "Uses `pdf2docx.Converter` to read the PDF layout and reconstruct headings, lists, inline formatting, and tables into a native DOCX document."),
         
        ("PDF Split and Merge (`split_pdf`, `merge_pdf`)", 
         "File: pdfapp/services/pdf_service.py", 
         "Uses `fitz (PyMuPDF)` to read the source PDF. In `split_pdf`, it extracts targeted page ranges and inserts them into a new document. In `merge_pdf`, it concatenates multiple document objects into one."),
         
        ("PDF Compression (`compress_pdf`)", 
         "File: pdfapp/services/compression.py", 
         "Uses `fitz (PyMuPDF)` to extract images from PDF page objects. It uses `Pillow (PIL)` to compress, downsample, and reduce image resolution, then replaces them back into the PDF container."),
         
        ("Text Replace in PDF (`replace_text_in_pdf`)", 
         "File: pdfapp/services/editor.py", 
         "Uses `fitz (PyMuPDF)` to search for coordinates of targeted text instances, draws whiteout rectangles over the original characters, and overlays the replacement text in matching fonts."),
         
        ("PDF to Excel Table Extraction (`convert_pdf_to_excel`)", 
         "File: pdfapp/services/excel_service.py", 
         "Uses `pdfplumber` to inspect the layout structure of pages, isolates grid lines to identify tables, and parses text cell-by-cell. It then uses `openpyxl` to populate a workbook sheet and writes the spreadsheet.")
    ]
    
    for title, source, desc in functions:
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(8)
        p_title.paragraph_format.space_after = Pt(2)
        p_title.paragraph_format.keep_with_next = True
        
        run_title = p_title.add_run(f"■ {title}")
        run_title.font.bold = True
        run_title.font.size = Pt(11)
        run_title.font.color.rgb = COLOR_PRIMARY
        
        p_src = doc.add_paragraph()
        p_src.paragraph_format.space_after = Pt(2)
        p_src.paragraph_format.left_indent = Inches(0.2)
        p_src.paragraph_format.keep_with_next = True
        run_src = p_src.add_run(source)
        run_src.font.italic = True
        run_src.font.size = Pt(9.5)
        run_src.font.color.rgb = COLOR_SECONDARY
        
        p_desc = doc.add_paragraph(desc)
        p_desc.paragraph_format.space_after = Pt(10)
        p_desc.paragraph_format.left_indent = Inches(0.2)
        p_desc.paragraph_format.line_spacing = 1.1

    doc.add_page_break()

    # ------------------ SECTION 4: INSTALLATION GUIDE ------------------
    add_heading_with_color(doc, "4. Package Setup & Installation Guide", 1, COLOR_PRIMARY)
    
    inst_p = doc.add_paragraph(
        "Follow these structured instructions to install and configure all required python packages, "
        "virtual environments, and system-level dependencies for DocuConverter Pro."
    )
    inst_p.paragraph_format.space_after = Pt(12)
    
    steps = [
        ("Step 1: System Prerequisites (Windows Server / PC)",
         "Because the platform uses high-fidelity Windows COM automation for Word and PowerPoint "
         "conversions, the server host environment MUST meet the following:\n"
         "• Operating System: Windows 10, Windows 11, or Windows Server 2016+.\n"
         "• Office Suite: Microsoft Word and Microsoft PowerPoint desktop applications must be "
         "installed and licensed on the machine. (Web or mobile editions will not work)."),
         
        ("Step 2: Python Environment Setup",
         "Open a Windows Command Prompt or PowerShell in the root project folder:\n"
         "1. Create a Python virtual environment to avoid package version conflicts:\n"
         "   python -m venv .venv\n"
         "2. Activate the virtual environment:\n"
         "   In Command Prompt (cmd.exe):  .venv\\Scripts\\activate.bat\n"
         "   In PowerShell (powershell.exe): .venv\\Scripts\\Activate.ps1"),
         
        ("Step 3: Package Installation",
         "With the virtual environment activated, install all dependencies by running:\n"
         "   pip install django pymupdf python-docx docxcompose mammoth htmldocx pdf2docx pdfplumber openpyxl pillow pywin32 opencv-python-headless\n\n"
         "Alternatively, if a requirements.txt file exists in the directory, you can run:\n"
         "   pip install -r requirements.txt"),
         
        ("Step 4: Register pywin32 System Post-Install COM Hooks",
         "The COM bridge package requires registering DLL dependencies with the Windows registry:\n"
         "   python .venv\\Scripts\\pywin32_postinstall.py -install"),
         
        ("Step 5: Run Database Migrations",
         "Prepare the SQLite session database and authentication models:\n"
         "   python manage.py migrate"),
         
        ("Step 6: Start the Server",
         "Launch the Django development server to bind the network ports:\n"
         "   python manage.py runserver 8000\n"
         "Open a browser and navigate to http://127.0.0.1:8000 to interact with the dashboard.")
    ]
    
    for step_title, step_desc in steps:
        p_st = doc.add_paragraph()
        p_st.paragraph_format.space_before = Pt(8)
        p_st.paragraph_format.space_after = Pt(4)
        p_st.paragraph_format.keep_with_next = True
        
        run_st = p_st.add_run(step_title)
        run_st.font.bold = True
        run_st.font.size = Pt(11)
        run_st.font.color.rgb = COLOR_PRIMARY
        
        p_sd = doc.add_paragraph(step_desc)
        p_sd.paragraph_format.space_after = Pt(12)
        p_sd.paragraph_format.left_indent = Inches(0.2)
        p_sd.paragraph_format.line_spacing = 1.1

    doc.add_page_break()

    # ------------------ SECTION 5: TROUBLESHOOTING ------------------
    add_heading_with_color(doc, "5. Common Configuration Troubleshooting", 1, COLOR_PRIMARY)
    
    ts_intro = doc.add_paragraph(
        "Refer to this list of typical configuration issues and solutions if you encounter setup errors:"
    )
    ts_intro.paragraph_format.space_after = Pt(12)
    
    troubleshoots = [
        ("1. Issue: 'pywin32 / win32com' fails to import or shows 'DLL load failed'",
         "Solution: This happens if the system environment path doesn't point to the pywin32 DLLs. Run the post-install script:\n"
         "   python .venv\\Scripts\\pywin32_postinstall.py -install\n"
         "If the issue persists, run the command in an Administrator shell."),
         
        ("2. Issue: Word COM conversion throws 'Word COM operation failed'",
         "Solution: Ensure that:\n"
         "• Microsoft Word is not running under a different user account or crashed in the background. Open Task Manager and end any stale 'WINWORD.EXE' processes.\n"
         "• Word is activated and has passed its initial setup screens. Start Word manually once, accept the license terms, and close it before starting the web server."),
         
        ("3. Issue: Page margins or header layouts are broken after merging DOCX files",
         "Solution: Ensure that `docxcompose` is installed. When using standard python-docx to concatenate, styles overlap. Docxcompose correctly segregates section margins, layout properties, and styling headers to prevent overlap.")
    ]
    
    for ts_title, ts_desc in troubleshoots:
        p_tst = doc.add_paragraph()
        p_tst.paragraph_format.space_before = Pt(6)
        p_tst.paragraph_format.space_after = Pt(2)
        p_tst.paragraph_format.keep_with_next = True
        
        run_tst = p_tst.add_run(ts_title)
        run_tst.font.bold = True
        run_tst.font.size = Pt(10.5)
        run_tst.font.color.rgb = COLOR_HIGHLIGHT
        
        p_tsd = doc.add_paragraph(ts_desc)
        p_tsd.paragraph_format.space_after = Pt(10)
        p_tsd.paragraph_format.left_indent = Inches(0.2)
        p_tsd.paragraph_format.line_spacing = 1.1

    # Save DOCX
    docx_path = os.path.abspath("media/packages_guide.docx")
    os.makedirs(os.path.dirname(docx_path), exist_ok=True)
    doc.save(docx_path)
    print(f"DOCX created successfully at: {docx_path}")
    return docx_path

def convert_to_pdf(docx_path):
    pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
    
    import pythoncom
    import win32com.client
    
    pythoncom.CoInitialize()
    word = None
    try:
        print("Launching Microsoft Word COM to export PDF...")
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        
        doc = word.Documents.Open(FileName=docx_path, ReadOnly=True, AddToRecentFiles=False)
        
        # Save as PDF format
        doc.ExportAsFixedFormat(
            OutputFileName=pdf_path,
            ExportFormat=17, # WD_EXPORT_FORMAT_PDF
            OpenAfterExport=False,
            OptimizeFor=0,
            Range=0,
            Item=0,
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=1,
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False
        )
        doc.Close(SaveChanges=False)
        print(f"PDF exported successfully at: {pdf_path}")
    except Exception as e:
        print(f"COM conversion failed: {e}")
        # Try a quick fallback using docx2pdf
        try:
            from docx2pdf import convert
            convert(docx_path, pdf_path)
            print(f"PDF created via docx2pdf fallback at: {pdf_path}")
        except Exception as f_err:
            print(f"Fallback also failed: {f_err}")
            raise e
    finally:
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()
    return pdf_path

if __name__ == "__main__":
    # If script runs inside Django, we might have different cwd.
    # Set CWD to wordpdf root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)
    
    docx_p = create_report()
    pdf_p = convert_to_pdf(docx_p)
    print(f"All done! PDF location: {pdf_p}")
