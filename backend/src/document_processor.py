import os
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import logging

logging.getLogger("pdfplumber").setLevel(logging.WARNING)

def extract_text_from_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        return f"❌ Error: File PDF '{pdf_path}' tidak ditemukan."
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"System: Gagal mengekstrak teks dengan pdfplumber: {str(e)}")

    if not text.strip():
        print(f"System: Tidak ada teks yang terdeteksi dalam {pdf_path} dengan pdfplumber. Mencoba OCR...")
        try:
            with open(pdf_path, "rb") as f:
                pdf_content = f.read()
            images = convert_from_bytes(pdf_content)
            for image in images:
                page_text = pytesseract.image_to_string(image, lang="eng+ind")
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"System: Gagal mengekstrak teks dengan OCR: {str(e)}")

    return text.strip() or ""

def extract_text(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        return f"❌ Error: Format file '{ext}' tidak didukung."