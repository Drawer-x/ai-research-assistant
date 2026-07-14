# pdf_parser.py

def extract_text_from_pdf(pdf_path: str) -> dict:
    result = {"title": "", "abstract": "", "full_text": "", "pages": []}
    try:
        import fitz
        with fitz.open(pdf_path) as document:
            pages = [page.get_text("text") for page in document]
        result["pages"] = pages
        result["full_text"] = "\n".join(pages)
        return result
    except Exception:
        return result
