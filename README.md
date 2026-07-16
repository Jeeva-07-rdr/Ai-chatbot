# DocuConverter Pro 📄➡️📝

DocuConverter Pro is a premium Django-based web application designed for high-fidelity document conversions and management. It uses Windows COM automation (via Microsoft Office desktop applications) to perform premium, native-quality conversions, with robust open-source library fallbacks.

---

## 🚀 Key Features

*   **PDF Tools**:
    *   **PDF to Word**: Converts PDFs back into editable Microsoft Word documents preserving tables, columns, and layout structure (using native Microsoft Word COM).
    *   **PDF to Excel**: Extracts tabular data into Excel files.
    *   **PDF Merge & Split**: Merges multiple PDFs or extracts specific pages/ranges.
    *   **PDF Compress**: Compresses and optimizes PDF files.
*   **Word Tools**:
    *   **Word to PDF**: High-fidelity export of DOCX files to PDF.
    *   **Word Merge & Split**: Combines or splits Word documents while keeping styling intact.
*   **Excel & PowerPoint Tools**:
    *   **Excel to PDF**: Converts sheets to PDFs.
    *   **PowerPoint to PDF & Word**: Exports slides to PDF or document layouts.
*   **Image Tools**:
    *   **Image to PDF**: Merges PNG/JPG images into a single PDF.
    *   **Format Converter**: Convert between JPEG and PNG.
*   **Conversion History**: Keeps a secure log of all successful conversions in a local MySQL database.

---

## 🛠️ Prerequisites

To run this project locally, you need:
1.  **Python (3.13.x or newer)**.
2.  **Microsoft Office** installed locally (Microsoft Word, Excel, and PowerPoint are required for high-fidelity COM automation).
3.  **MySQL Database Server** (normally run via XAMPP, WampServer, or local MySQL Service).
4.  **Windows OS** (required for COM automation).

---

## ⚙️ Setup & Installation

Follow these steps to set up and run the project locally:

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd WordToPDF_Web
```

### 2. Create and Activate the Virtual Environment
Create a clean local environment:
```powershell
# Create the environment
python -m venv .venv

# Activate on Windows (PowerShell)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
Install all required Python packages:
```powershell
pip install -r wordpdf/requirements.txt
```

### 4. Setup MySQL Database
1. Start your MySQL Server (e.g. from the XAMPP Control Panel).
2. Create a new database named `docuconverter_db`:
   ```sql
   CREATE DATABASE docuconverter_db;
   ```
3. *(Optional)* If your local MySQL requires a password or runs on a different port, update the credentials in `wordpdf/wordpdf/settings.py` under `DATABASES`.

### 5. Apply Migrations
Set up your database tables by running:
```powershell
python wordpdf/manage.py migrate
```

### 6. Start the Server
Run the Django local development server:
```powershell
python wordpdf/manage.py runserver
```
Open **`http://127.0.0.1:8000/`** in your web browser to start converting!

---

## ⚠️ Important: PDF to Word Automation Warning (Windows)

When Microsoft Word attempts to open a PDF in a headless/automated server environment for the first time, it might trigger a hidden dialog box stating: *"Word will now convert your PDF to an editable Word document..."*.

Because the server runs Word in the background, this window is invisible and will hang the application indefinitely.

### How to Fix / Avoid Hanging:
To bypass this warning dialog automatically, run the following command in PowerShell as Administrator to configure the Windows registry:

```powershell
# Suppress the PDF conversion warning dialog in Microsoft Word
New-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\Word\Options" -Name "DisableConvertPdfWarning" -Value 1 -PropertyType DWORD -Force
```
This configuration is already preset on this development environment.
