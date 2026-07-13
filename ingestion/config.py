import os

DATA_DIR      = "data"
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
PDF_DIR       = os.path.join(DATA_DIR, "pdfs")
PDF_RAW_DIR   = os.path.join(PDF_DIR, "raw")
EXTRACTED_TEXT_DIR = os.path.join(PDF_DIR, "extracted_text")
IMAGES_DIR    = os.path.join(PDF_DIR, "images")
VISUALS_DIR   = os.path.join(PDF_DIR, "visuals")

RAW_PAPERS_FILE   = os.path.join(PROCESSED_DIR, "oral_cancer_papers.json")
CLEAN_PAPERS_FILE = os.path.join(PROCESSED_DIR, "oral_cancer_papers_clean.json")
FINAL_PAPERS_FILE = os.path.join(PROCESSED_DIR, "oral_cancer_papers_final.json")

for _dir in (PROCESSED_DIR, PDF_RAW_DIR, EXTRACTED_TEXT_DIR, IMAGES_DIR, VISUALS_DIR):
    os.makedirs(_dir, exist_ok=True)
