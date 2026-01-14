# main.py
import argparse
import shutil
import os
from config import Config
from core.loader import PDFLoader
from core.extractor import PaddleLayoutExtractor
from core.builder import PPTXBuilder

def cleanup():
    """Removes temp assets."""
    if os.path.exists(Config.TEMP_DIR):
        shutil.rmtree(Config.TEMP_DIR)
        os.makedirs(Config.TEMP_DIR)

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to editable PPTX using OCR.")
    parser.add_argument("input_pdf", type=str, help="Path to input PDF")
    parser.add_argument("output_pptx", type=str, help="Path to save output PPTX")
    args = parser.parse_args()

    # 1. Initialize Components
    loader = PDFLoader(dpi=Config.DPI)
    extractor = PaddleLayoutExtractor(lang=Config.OCR_LANG)
    builder = PPTXBuilder()

    # 2. Load Images
    images = loader.load_pdf(args.input_pdf)
    
    # 3. Process each page
    for i, image in enumerate(images):
        print(f"--- Processing Page {i+1}/{len(images)} ---")
        
        # Extract Layout (Text + Bounding Boxes + Types + Cleaned Image)
        result = extractor.extract(image)
        elements = result['elements']
        cleaned_image = result['cleaned_image']
        
        # Build Slide
        builder.create_slide(image, elements, cleaned_image, page_num=i)

    # 4. Save and Clean
    builder.save(args.output_pptx)
    cleanup()

if __name__ == "__main__":
    main()
