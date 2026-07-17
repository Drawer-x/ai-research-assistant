import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.models.paper import Paper
from app.models.relation import PaperRelation
from app.models.tag import Tag
from app.models.user import User
from app.services.graph_service import build_paper_graph


class GraphServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.owner = User(username="owner", email="owner@example.com", password_hash="hash")
        self.other = User(username="other", email="other@example.com", password_hash="hash")
        self.db.add_all([self.owner, self.other])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def paper(self, title: str, *, user=None, abstract="", full_text="", tags=()) -> Paper:
        paper = Paper(
            user_id=(user or self.owner).id,
            title=title,
            abstract=abstract,
            full_text=full_text,
            pdf_path="uploads/test.pdf",
        )
        for name in tags:
            user_id = (user or self.owner).id
            tag = self.db.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
            paper.tags.append(tag or Tag(user_id=user_id, name=name))
        self.db.add(paper)
        self.db.commit()
        return paper

    def test_same_title_creates_single_inferred_edge(self):
        first = self.paper("相同标题")
        second = self.paper("相同标题")
        graph = build_paper_graph(self.db, self.owner.id)
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual({graph["edges"][0]["source"], graph["edges"][0]["target"]}, {first.id, second.id})
        self.assertTrue(graph["edges"][0]["inferred"])

    def test_similar_topic_uses_chinese_phrases_and_tags(self):
        first = self.paper("时间序列预测", abstract="Transformer 模型预测", tags=("深度学习",))
        second = self.paper("时间序列建模", abstract="Transformer 预测方法", tags=("深度学习",))
        graph = build_paper_graph(self.db, self.owner.id)
        self.assertEqual(len(graph["edges"]), 1)
        self.assertGreater(graph["edges"][0]["confidence"], 0.08)

    def test_unrelated_papers_have_no_edge(self):
        self.paper("量子纠缠实验", abstract="光子测量")
        self.paper("古典诗歌研究", abstract="唐代文学")
        self.assertEqual(build_paper_graph(self.db, self.owner.id)["edges"], [])

    def test_manual_relation_blocks_inference_and_duplicates_are_removed(self):
        first = self.paper("相同标题")
        second = self.paper("相同标题")
        self.db.add_all([
            PaperRelation(source_paper_id=first.id, target_paper_id=second.id, relation_type="citation"),
            PaperRelation(source_paper_id=first.id, target_paper_id=second.id, relation_type="citation"),
        ])
        self.db.commit()
        edges = build_paper_graph(self.db, self.owner.id)["edges"]
        self.assertEqual(len(edges), 1)
        self.assertFalse(edges[0]["inferred"])

    def test_user_isolation_excludes_nodes_and_cross_user_relations(self):
        owned = self.paper("Owner Paper")
        foreign = self.paper("Owner Paper", user=self.other)
        self.db.add(PaperRelation(source_paper_id=owned.id, target_paper_id=foreign.id, relation_type="citation"))
        self.db.commit()
        graph = build_paper_graph(self.db, self.owner.id)
        self.assertEqual([node["id"] for node in graph["nodes"]], [owned.id])
        self.assertEqual(graph["edges"], [])


if __name__ == "__main__":
    unittest.main()
