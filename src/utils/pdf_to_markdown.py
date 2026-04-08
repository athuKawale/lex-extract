import os
import pymupdf.layout
import pymupdf4llm
from pathlib import Path
import glob

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Define directories
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = ROOT_DIR / "input"
MARKDOWN_DIR = ROOT_DIR / "markdown_output"

def pdf_to_markdown(pdf_path, output_dir):
    print(f"Converting PDF to Markdown: {pdf_path}")
    doc = pymupdf.open(pdf_path)
    md = pymupdf4llm.to_markdown(doc, header=False, footer=False, page_separators=True, ignore_images=True, write_images=False, image_path=None)
    md_cleaned = md.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='ignore')
    output_path = Path(output_dir) / Path(doc.name).stem
    Path(output_path).with_suffix(".md").write_bytes(md_cleaned.encode('utf-8'))

def pdfs_to_markdowns(path_pattern=None, overwrite: bool = False):
    if path_pattern is None:
        path_pattern = f"{DOCS_DIR}/*.pdf"
    output_dir = Path(MARKDOWN_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(Path().glob(path_pattern) if "*" not in str(path_pattern) else map(Path, glob.glob(str(path_pattern))))
    print(f"Found {len(pdf_files)} PDFs to process.")

    for pdf_path in pdf_files:
        md_path = (output_dir / pdf_path.stem).with_suffix(".md")
        if overwrite or not md_path.exists():
            pdf_to_markdown(pdf_path, output_dir)
        else:
            print(f"Markdown already exists for {pdf_path.name}, skipping.")