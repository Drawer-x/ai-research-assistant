from sqlalchemy import select
from app.models.paper_external_source import PaperExternalSource

class PaperContentUnavailable(ValueError): pass
def get_paper_analysis_content(db,paper,user_id):
    if paper.user_id!=user_id: raise PaperContentUnavailable("paper is not accessible")
    full_text=paper.full_text or ""
    if full_text.strip():
        source="external_pdf" if str(paper.pdf_path).startswith("external://") else "local_pdf"
        return {"text":full_text,"analysis_scope":"full_text","source":source}
    if not str(paper.pdf_path).startswith("external://"):
        # Preserve the pre-Sprint-4 local-PDF behavior: the existing AI adapter
        # supplies its stable fallback when parsing produced no text.
        return {"text":"","analysis_scope":"full_text","source":"local_pdf"}
    source=db.scalar(select(PaperExternalSource).where(PaperExternalSource.paper_id==paper.id,PaperExternalSource.user_id==user_id))
    abstract=(source.abstract if source else None) or paper.abstract
    if not abstract:raise PaperContentUnavailable("该外部论文没有可分析的摘要或全文，请先补传 PDF")
    return {"text":abstract,"analysis_scope":"abstract_only","source":source.provider if source else "metadata"}
