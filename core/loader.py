# core/loader.py
from pdf2image import convert_from_path
from typing import List
from PIL import Image

class PDFLoader:
    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def load_pdf(self, pdf_path: str) -> List[Image.Image]:
        """Converts a PDF into a list of PIL Images."""
        print(f"[INFO] Converting PDF: {pdf_path}...")
        try:
            images = convert_from_path(pdf_path, dpi=self.dpi)
            print(f"[INFO] Converted {len(images)} pages.")
            return images
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF. Ensure Poppler is installed. Error: {e}")
