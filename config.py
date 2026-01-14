# config.py
import os

class Config:
    OCR_LANG = 'en'
    # DPI for PDF to Image conversion (Higher = better OCR, slower speed)
    DPI = 300 
    # Temp folder for cropped images
    TEMP_DIR = "temp_assets"
    
    # Create temp dir if not exists
    os.makedirs(TEMP_DIR, exist_ok=True)
