from sqlalchemy import select
from app.models.paper_external_source import PaperExternalSource

class PaperContentUnavailable(ValueError): pass
def get_paper_analysis_content(db,paper,user_id):
    if paper.user_id!=user_id: raise PaperContentUnavailable("paper is not accessible")
    if not str(paper.pdf_path).startswith("external://"):
        # Preserve the pre-Sprint-4 local-PDF behavior: the existing AI adapter
        # supplies its stable fallback when parsing produced no text.
        return {"text":paper.full_text or "","analysis_scope":"full_text","source":"local_pdf"}
    source=db.scalar(select(PaperExternalSource).where(PaperExternalSource.paper_id==paper.id,PaperExternalSource.user_id==user_id))
    abstract=(source.abstract if source else None) or paper.abstract
    if not abstract:raise PaperContentUnavailable("external paper has no analyzable abstract")
    return {"text":abstract,"analysis_scope":"abstract_only","source":source.provider}
