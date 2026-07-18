import pickle
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services import embedding_service, vector_store
from app.services.ai_errors import AIErrorReason
from app.services.embedding_service import EmbeddingServiceError, get_embeddings
from app.services.text_splitter import split_text
from app.services.vector_store import (
    VectorDimensionError,
    VectorStoreCorruptError,
    VectorStoreNotFoundError,
    save_vector_store,
    search_similar_chunks,
    search_similar_chunks_with_scores,
)


class MaliciousMetadata:
    def __reduce__(self):
        return print, ("must not execute",)


class FakeEmbeddingsAPI:
    def __init__(self):
        self.inputs = []

    def create(self, *, model, input):
        self.inputs.append(list(input))
        items = [SimpleNamespace(index=index, embedding=[float(value), float(value + 1)]) for index, value in enumerate(range(len(input)))]
        return SimpleNamespace(data=list(reversed(items)))


class EmbeddingServiceTests(unittest.TestCase):
    def tearDown(self):
        embedding_service._get_client.cache_clear()

    @patch("app.services.embedding_service._get_client")
    def test_batches_once_per_group_and_preserves_input_order(self, get_client):
        api = FakeEmbeddingsAPI()
        get_client.return_value = SimpleNamespace(embeddings=api)
        with patch.object(embedding_service.settings, "embedding_batch_size", 2):
            result = get_embeddings(["a", "b", "c", "d", "e"])
        self.assertEqual(api.inputs, [["a", "b"], ["c", "d"], ["e"]])
        self.assertEqual(result, [[0.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 2.0], [0.0, 1.0]])

    @patch("app.services.embedding_service._get_client")
    def test_blank_text_rejects_whole_batch_before_provider_call(self, get_client):
        with self.assertRaisesRegex(ValueError, "位置：1"):
            get_embeddings(["valid", "   ", "also valid"])
        get_client.assert_not_called()

    @patch("app.services.embedding_service._get_client")
    def test_empty_provider_response_is_controlled(self, get_client):
        api = SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[]))
        get_client.return_value = SimpleNamespace(embeddings=api)
        with self.assertRaises(EmbeddingServiceError) as caught:
            get_embeddings(["text"])
        self.assertEqual(caught.exception.reason, AIErrorReason.EMPTY_RESPONSE)

    @patch("app.services.embedding_service._get_client")
    def test_partial_provider_count_is_malformed(self, get_client):
        item = SimpleNamespace(index=0, embedding=[0.0, 1.0])
        api = SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[item]))
        get_client.return_value = SimpleNamespace(embeddings=api)
        with self.assertRaises(EmbeddingServiceError) as caught:
            get_embeddings(["first", "second"])
        self.assertEqual(caught.exception.reason, AIErrorReason.MALFORMED_RESPONSE)

    @patch("app.services.embedding_service._get_client")
    def test_mixed_missing_provider_indices_are_rejected(self, get_client):
        items = [
            SimpleNamespace(index=0, embedding=[0.0, 1.0]),
            SimpleNamespace(index=None, embedding=[1.0, 2.0]),
        ]
        get_client.return_value.embeddings.create.return_value = SimpleNamespace(data=items)
        with self.assertRaises(EmbeddingServiceError) as caught:
            get_embeddings(["first", "second"])
        self.assertEqual(caught.exception.reason, AIErrorReason.MALFORMED_RESPONSE)

    def test_missing_key_has_typed_reason(self):
        embedding_service._get_client.cache_clear()
        with patch.object(embedding_service.settings, "ecnu_api_key", None):
            with self.assertRaises(EmbeddingServiceError) as caught:
                embedding_service._get_client()
        self.assertEqual(caught.exception.reason, AIErrorReason.MISSING_CONFIGURATION)

    @patch("app.services.embedding_service._get_client")
    def test_timeout_is_mapped(self, get_client):
        get_client.return_value.embeddings.create.side_effect = TimeoutError("provider detail")
        with self.assertRaises(EmbeddingServiceError) as caught:
            get_embeddings(["text"])
        self.assertEqual(caught.exception.reason, AIErrorReason.TIMEOUT)
        self.assertNotIn("provider detail", str(caught.exception))


class TextSplitterTests(unittest.TestCase):
    def test_rejects_invalid_parameters(self):
        for chunk_size, overlap in ((0, 0), (10, -1), (10, 10)):
            with self.subTest(chunk_size=chunk_size, overlap=overlap), self.assertRaises(ValueError):
                split_text("text", chunk_size, overlap)

    def test_avoids_blank_chunks_and_prefers_sentence_boundary(self):
        chunks = split_text("第一句。第二句。\n\n第三段内容。", chunk_size=10, overlap=2)
        self.assertTrue(chunks)
        self.assertTrue(all(chunk.strip() for chunk in chunks))
        self.assertLessEqual(max(map(len, chunks)), 10)


class VectorStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vector_dir = Path(self.temp_dir.name)
        self.vector_patch = patch.object(vector_store, "VECTOR_DIR", self.vector_dir)
        self.vector_patch.start()

    def tearDown(self):
        self.vector_patch.stop()
        self.temp_dir.cleanup()

    def test_save_search_and_trace_metadata(self):
        save_vector_store(1, ["alpha", "beta"], [[0.0, 0.0], [10.0, 10.0]])
        results = search_similar_chunks_with_scores(1, [0.0, 0.0], top_k=2)
        self.assertEqual(results[0].text, "alpha")
        self.assertEqual(results[0].chunk_index, 0)
        self.assertEqual(results[0].score, 0.0)
        self.assertEqual(search_similar_chunks(1, [0.0, 0.0], 1), ["alpha"])

    def test_owned_store_rejects_wrong_user_source_and_legacy_metadata(self):
        save_vector_store(
            1,
            ["owner evidence"],
            [[0.0, 0.0]],
            owner_id=7,
            source_text="owner paper",
        )
        self.assertEqual(
            search_similar_chunks(
                1,
                [0.0, 0.0],
                owner_id=7,
                source_text="owner paper",
            ),
            ["owner evidence"],
        )
        with self.assertRaises(VectorStoreCorruptError):
            search_similar_chunks(1, [0.0, 0.0], owner_id=8, source_text="owner paper")
        with self.assertRaises(VectorStoreCorruptError):
            search_similar_chunks(1, [0.0, 0.0], owner_id=7, source_text="different paper")

        (self.vector_dir / "1.pkl").write_bytes(pickle.dumps(["legacy evidence"]))
        self.assertEqual(search_similar_chunks(1, [0.0, 0.0]), ["legacy evidence"])
        with self.assertRaisesRegex(VectorStoreCorruptError, "归属信息"):
            search_similar_chunks(1, [0.0, 0.0], owner_id=7, source_text="owner paper")

    def test_chunk_vector_count_mismatch(self):
        with self.assertRaisesRegex(ValueError, "分块数与向量数不一致"):
            save_vector_store(1, ["a", "b"], [[0.0, 0.0]])

    def test_vector_dimension_mismatch_on_save_and_search(self):
        with self.assertRaises(VectorDimensionError):
            save_vector_store(1, ["a", "b"], [[0.0], [1.0, 2.0]])
        save_vector_store(1, ["a"], [[0.0, 1.0]])
        with self.assertRaises(VectorDimensionError):
            search_similar_chunks(1, [0.0], 1)

    def test_repeated_save_replaces_both_files(self):
        save_vector_store(1, ["old"], [[0.0, 0.0]])
        save_vector_store(1, ["new"], [[1.0, 1.0]])
        self.assertEqual(search_similar_chunks(1, [1.0, 1.0], 1), ["new"])
        self.assertFalse(list(self.vector_dir.glob("*.tmp")))
        self.assertFalse(list(self.vector_dir.glob("*.bak")))

    def test_concurrent_same_paper_saves_leave_a_complete_pair(self):
        def save(value: float) -> None:
            save_vector_store(1, [f"chunk {value}"], [[value, value]])

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(save, [float(value) for value in range(8)]))
        result = search_similar_chunks(1, [0.0, 0.0], 1)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("chunk "))
        self.assertTrue((self.vector_dir / "1.index").exists())
        self.assertTrue((self.vector_dir / "1.pkl").exists())

    def test_failed_pair_replace_restores_previous_store(self):
        save_vector_store(1, ["old"], [[0.0, 0.0]])
        real_replace = vector_store.os.replace
        data_path = self.vector_dir / "1.pkl"

        def fail_second_replace(source, target):
            if str(source).endswith(".pkl.tmp") and Path(target) == data_path:
                raise OSError("simulated replace failure")
            return real_replace(source, target)

        with patch("app.services.vector_store.os.replace", side_effect=fail_second_replace):
            with self.assertRaises(OSError):
                save_vector_store(1, ["new"], [[1.0, 1.0]])
        self.assertEqual(search_similar_chunks(1, [0.0, 0.0], 1), ["old"])
        self.assertFalse(list(self.vector_dir.glob("*.tmp")))
        self.assertFalse(list(self.vector_dir.glob("*.bak")))

    def test_failed_backup_step_keeps_previous_pair(self):
        save_vector_store(1, ["old"], [[0.0, 0.0]])
        real_replace = vector_store.os.replace
        data_path = self.vector_dir / "1.pkl"

        def fail_data_backup(source, target):
            if Path(source) == data_path and str(target).endswith(".bak"):
                raise OSError("simulated backup failure")
            return real_replace(source, target)

        with patch("app.services.vector_store.os.replace", side_effect=fail_data_backup):
            with self.assertRaises(OSError):
                save_vector_store(1, ["new"], [[1.0, 1.0]])
        self.assertEqual(search_similar_chunks(1, [0.0, 0.0], 1), ["old"])

    def test_missing_partial_and_corrupt_stores_are_distinct(self):
        with self.assertRaises(VectorStoreNotFoundError):
            search_similar_chunks(1, [0.0], 1)
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        (self.vector_dir / "1.pkl").write_bytes(pickle.dumps(["orphan"]))
        with self.assertRaises(VectorStoreCorruptError):
            search_similar_chunks(1, [0.0], 1)

    def test_pickle_globals_are_rejected_without_execution(self):
        save_vector_store(1, ["valid"], [[0.0]])
        (self.vector_dir / "1.pkl").write_bytes(pickle.dumps(MaliciousMetadata()))
        with patch("builtins.print") as print_mock:
            with self.assertRaises(VectorStoreCorruptError):
                search_similar_chunks(1, [0.0], 1)
        print_mock.assert_not_called()
        (self.vector_dir / "1.pkl").unlink()
        save_vector_store(1, ["valid"], [[0.0]])
        (self.vector_dir / "1.pkl").write_bytes(b"not a pickle")
        with self.assertRaises(VectorStoreCorruptError):
            search_similar_chunks(1, [0.0], 1)


if __name__ == "__main__":
    unittest.main()
