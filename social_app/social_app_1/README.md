# Document Data Collector

A Streamlit application that processes images and PDFs to extract information using OCR (Optical Character Recognition) technology.

## Features

- Supports PDF and image files (PNG, JPG, JPEG)
- Extracts:
  - Income (in AED)
  - Family Size
  - Address
- Supports both Arabic and English text
- Results are stored in a DataFrame and can be downloaded as CSV

## Prerequisites

- Python 3.7+
- Tesseract OCR installed on your system
- Poppler (for PDF processing)

### Installing Tesseract

#### macOS
```bash
brew install tesseract
brew install tesseract-lang  # for additional languages
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-ara  # for Arabic support
```

#### Windows
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Installing Poppler

#### macOS
```bash
brew install poppler
```

#### Ubuntu/Debian
```bash
sudo apt-get install poppler-utils
```

## Installation

1. Clone this repository
2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Upload a PDF or image file using the file uploader

4. Click "Process Document" to extract information

5. View the results in the table below

6. Download the results as CSV using the download button

## Notes

- The application uses Tesseract OCR with both Arabic and English language support
- For best results, ensure your documents are clear and well-scanned
- The application will automatically detect the language of the document 