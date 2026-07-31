from app.models.user import User
from app.models.paper import Paper
from app.models.tag import Tag, paper_tags
from app.models.summary import AISummary
from app.models.relation import PaperRelation
from app.models.research_plan import ResearchPlan
from app.models.qa_record import QARecord
from app.models.comparison import PaperComparison
from app.models.paper_external_source import PaperExternalSource
from app.models.paper_recommendation import PaperRecommendation

__all__ = [
    "User", "Paper", "Tag", "paper_tags", "AISummary", "PaperRelation",
    "ResearchPlan", "QARecord", "PaperComparison", "PaperExternalSource", "PaperRecommendation",
]
