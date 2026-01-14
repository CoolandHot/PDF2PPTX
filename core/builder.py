# core/builder.py
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
from config import Config

class PPTXBuilder:
    def __init__(self):
        self.prs = Presentation()
        # Remove default blank slide
        if len(self.prs.slides) > 0:
            xml_slides = self.prs.slides._sldIdLst
            slides = list(xml_slides)
            xml_slides.remove(slides[0])

    def _pixels_to_inches(self, px_val, img_dim_px, slide_dim_inch):
        """
        Converts pixel coordinate to PPTX inches using ratio mapping.
        Formula: (Value_Px / Total_Img_Px) * Total_Slide_Inches
        """
        return (px_val / img_dim_px) * slide_dim_inch

    def create_slide(self, original_image: Image.Image, elements: list, cleaned_image: Image.Image, page_num: int):
        """
        Creates a single slide with a cleaned background and overlaid text.
        """
        img_w, img_h = original_image.size
        
        # 1. Configure Slide Dimensions
        slide_width_inch = 10.0
        aspect_ratio = img_h / img_w
        slide_height_inch = slide_width_inch * aspect_ratio
        
        self.prs.slide_width = Inches(slide_width_inch)
        self.prs.slide_height = Inches(slide_height_inch)
        
        # 2. Add a blank slide layout
        blank_slide_layout = self.prs.slide_layouts[6] 
        slide = self.prs.slides.add_slide(blank_slide_layout)

        # 3. Add Cleaned Image as Background (Layer 0)
        bg_path = os.path.join(Config.TEMP_DIR, f"bg_p{page_num}.png")
        cleaned_image.save(bg_path)
        slide.shapes.add_picture(bg_path, 0, 0, Inches(slide_width_inch), Inches(slide_height_inch))

        # 4. Process Elements (Overlay Layer)
        for elem in elements:
            bbox = elem['bbox'] # [x1, y1, x2, y2]
            etype = elem['type']
            
            if etype not in ['text', 'title', 'header', 'footer']:
                # Skip non-text types as they are already in the background image
                continue

            content = elem.get('content', '')
            if not content: continue
            
            # Calculate PPTX coordinates
            x1, y1, x2, y2 = bbox
            w_px = x2 - x1
            h_px = y2 - y1
            
            left = Inches(self._pixels_to_inches(x1, img_w, slide_width_inch))
            top = Inches(self._pixels_to_inches(y1, img_h, slide_height_inch))
            width = Inches(self._pixels_to_inches(w_px, img_w, slide_width_inch))
            height = Inches(self._pixels_to_inches(h_px, img_h, slide_height_inch))
            
            # Insert Text Box
            txBox = slide.shapes.add_textbox(left, top, width, height)
            tf = txBox.text_frame
            tf.word_wrap = True
            
            p = tf.paragraphs[0]
            p.text = content
            
            # Dynamic Font Sizing (Heuristic)
            if h_px > 0:
                num_lines = max(1, content.count('\n') + 1)
                approx_pt = (self._pixels_to_inches(h_px, img_h, slide_height_inch) * 72) / num_lines
                p.font.size = Pt(min(max(approx_pt * 0.8, 8), 40))


    def save(self, output_path: str):
        self.prs.save(output_path)
        print(f"[SUCCESS] Saved PPTX to {output_path}")
