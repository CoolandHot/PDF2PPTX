# core/extractor.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np
from paddleocr import PPStructure, PaddleOCR
from PIL import Image
import os
import cv2

class BaseLayoutExtractor(ABC):
    """Interface for Layout Extraction (Paddle, Qwen-VL, etc.)"""
    @abstractmethod
    def extract(self, image: Image.Image) -> Dict[str, Any]:
        """
        Must return a dict.
        Format: {
            'elements': [{'type': 'text|figure', 'bbox': [x1, y1, x2, y2], 'content': 'string'}],
            'cleaned_image': PIL.Image
        }
        """
        pass

class PaddleLayoutExtractor(BaseLayoutExtractor):
    def __init__(self, lang: str = 'en'):
        print("[INFO] Initializing PaddleOCR Engines...")
        # engine for layout analysis
        self.layout_engine = PPStructure(show_log=False, image_orientation=False, lang=lang)
        # engine for fallback OCR on figure regions
        self.ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def _clean_image(self, img_np: np.ndarray, elements: List[Dict[str, Any]]) -> Image.Image:
        """Removes text regions from the image using advanced context-aware filling."""
        h, w = img_np.shape[:2]
        cleaned = img_np.copy()
        mask = np.zeros((h, w), dtype=np.uint8)
        
        text_elements = [e for e in elements if e['type'] in ['text', 'title', 'header', 'footer']]
        
        for elem in text_elements:
            x1, y1, x2, y2 = map(int, elem['bbox'])
            
            # 1. Increased Dilation: Aggressively capture anti-aliasing (8px at 300DPI)
            dilation = 8
            dx1, dy1 = max(0, x1 - dilation), max(0, y1 - dilation)
            dx2, dy2 = min(w, x2 + dilation), min(h, y2 + dilation)
            
            # 2. Context Analysis
            context_pad = 15
            cx1, cy1 = max(0, dx1 - context_pad), max(0, dy1 - context_pad)
            cx2, cy2 = min(w, dx2 + context_pad), min(h, dy2 + context_pad)
            
            top_strip = img_np[cy1:dy1, cx1:cx2]
            bot_strip = img_np[dy2:cy2, cx1:cx2]
            lft_strip = img_np[dy1:dy2, cx1:dx1]
            rgt_strip = img_np[dy1:dy2, dx2:cx2]
            
            ring_pixels = []
            for strip in [top_strip, bot_strip, lft_strip, rgt_strip]:
                if strip.size > 0:
                    ring_pixels.append(strip.reshape(-1, 3))
            
            if ring_pixels:
                all_ring = np.concatenate(ring_pixels, axis=0)
                median_color = np.median(all_ring, axis=0)
                std_dev = np.std(all_ring, axis=0)
                
                # 3. Decision: Simple Fill vs Inpaint
                if np.mean(std_dev) < 20:
                    cv2.rectangle(cleaned, (dx1, dy1), (dx2, dy2), median_color.tolist(), -1)
                    # Add to mask for a light smoothing pass later
                    cv2.rectangle(mask, (dx1, dy1), (dx2, dy2), 255, -1)
                else:
                    cv2.rectangle(mask, (dx1, dy1), (dx2, dy2), 255, -1)

        # 4. Final Inpainting Pass
        if np.any(mask):
            cleaned = cv2.inpaint(cleaned, mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
            
            # 5. Smoothing Pass (Blend edges)
            # Create a blurred version of the cleaned image
            blurred = cv2.GaussianBlur(cleaned, (5, 5), 0)
            # Use a slightly dilated version of the mask edges to blend
            edge_mask = cv2.Canny(mask, 100, 200)
            edge_mask = cv2.dilate(edge_mask, np.ones((3, 3), np.uint8), iterations=1)
            edge_mask_3d = cv2.merge([edge_mask, edge_mask, edge_mask]) / 255.0
            
            # Blend blurred edges into cleaned image
            cleaned = (cleaned * (1 - edge_mask_3d) + blurred * edge_mask_3d).astype(np.uint8)
            
        return Image.fromarray(cleaned)

    def extract(self, image: Image.Image) -> Dict[str, Any]:
        img_np = np.array(image)
        layout_results = self.layout_engine(img_np)
        
        extracted_elements = []
        
        for region in layout_results:
            r_type = region.get('type', 'text').lower()
            bbox = region.get('bbox') # [x1, y1, x2, y2]
            
            if r_type == 'figure':
                # Check if this "figure" actually contains text
                x1, y1, x2, y2 = bbox
                h, w = img_np.shape[:2]
                x1, y1 = max(0, int(x1)), max(0, int(y1))
                x2, y2 = min(w, int(x2)), min(h, int(y2))
                
                if x2 > x1 and y2 > y1:
                    crop = img_np[y1:y2, x1:x2]
                    ocr_res = self.ocr_engine.ocr(crop, cls=True)
                    
                    if ocr_res and ocr_res[0]:
                        for line in ocr_res[0]:
                            l_bbox, (text, conf) = line
                            l_coords = np.array(l_bbox)
                            lx1, ly1 = np.min(l_coords, axis=0)
                            lx2, ly2 = np.max(l_coords, axis=0)
                            
                            extracted_elements.append({
                                'type': 'text',
                                'bbox': [x1 + lx1, y1 + ly1, x1 + lx2, y1 + ly2],
                                'content': text,
                                'font_size_px': (ly2 - ly1)
                            })
                    else:
                        extracted_elements.append({
                            'type': 'figure',
                            'bbox': bbox,
                            'content': None
                        })
            else:
                # Standard text block from PP-Structure
                # We split these into individual lines to match font sizes more accurately
                for line in region.get('res', []):
                    text = line.get('text', '')
                    if not text.strip(): continue
                    
                    l_region = np.array(line.get('text_region'))
                    lx1, ly1 = np.min(l_region, axis=0)
                    lx2, ly2 = np.max(l_region, axis=0)
                    
                    extracted_elements.append({
                        'type': r_type,
                        'bbox': [lx1, ly1, lx2, ly2],
                        'content': text,
                        'font_size_px': (ly2 - ly1)
                    })


        # Generate cleaned image (text removed)
        cleaned_image = self._clean_image(img_np, extracted_elements)

        return {
            'elements': extracted_elements,
            'original_image': image,
            'cleaned_image': cleaned_image
        }


class QwenVLExtractor(BaseLayoutExtractor):
    def extract(self, image: Image.Image) -> Dict[str, Any]:
        raise NotImplementedError("Qwen-VL implementation pending.")

