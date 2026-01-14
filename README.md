# PDF2PPTX: PDF to Editable PPTX Converter

PDF2PPTX is a powerful tool designed to convert PDF documents into editable PowerPoint (.pptx) presentations. Unlike simple conversion tools, it uses OCR and layout analysis to distinguish between text blocks and figures, ensuring that text remains editable and images are correctly placed.

## 🚀 Features

- **High-Resolution Conversion**: Efficiently converts PDF pages to high-quality images using `pdf2image`.
- **Intelligent Layout Analysis**: Leverages PaddleOCR (PP-Structure) to identify and classify document elements (text, titles, figures, etc.).
- **Hybrid OCR Strategy**: Automatically detects and OCRs text within region-misclassified "figures", ensuring scanned PDFs become fully editable.
- **Precise Coordinate Mapping**: Automatically scales pixel coordinates from OCR to PPTX inches for accurate layout reproduction.
- **Editable Content**: Text blocks are converted into editable PPTX text boxes with heuristic font sizing.
- **Figure Extraction**: Automatically crops and inserts figures/images into slides.
- **Modular Architecture**: Easy to extend or swap components (e.g., adding Vision-Language Models like Qwen-VL).

## 🏗 Project Architecture

```text
pdf2pptx/
├── main.py                # Entry point & CLI
├── config.py              # Centralized configuration
├── requirements.txt       # Python dependencies
└── core/
    ├── loader.py          # PDF to Image conversion
    ├── extractor.py       # OCR and Layout extraction logic
    └── builder.py         # PPTX construction and coordinate scaling
```

## 🛠 Prerequisites

### System Dependencies (Poppler)
The tool requires `poppler-utils` for PDF processing.

```bash
conda create -n pdf2pptx  -c conda-forge poppler pip python=3.12 -y
conda activate pdf2pptx
```

## 📦 Installation

1. Clone or download this project.
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

## 🖥 Usage

Run the converter from the command line:

```bash
python main.py <input_pdf_path> <output_pptx_path>
```

**Example:**
```bash
python main.py test.pdf output.pptx
```

## ⚙ Configuration

Settings can be adjusted in `config.py`:
- `OCR_LANG`: Set to your preferred language (e.g., 'en', 'ch').
- `DPI`: Adjust image resolution for OCR (default is 300).
- `TEMP_DIR`: Path for temporary assets during processing.

## ⚖ License
This project is open-source and available under the MIT License.
