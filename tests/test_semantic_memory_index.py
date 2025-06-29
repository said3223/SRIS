import os
import sys
import types
from unittest.mock import patch
import pytest

def setup_dummy_llama(monkeypatch):
    core = types.ModuleType("llama_index.core")
    class DummyDocument:
        def __init__(self, text, metadata=None):
            self.text = text
            self.metadata = metadata or {}
    class DummyStorageContext:
        @classmethod
        def from_defaults(cls, persist_dir=None):
            return cls()
        def persist(self, persist_dir):
            os.makedirs(persist_dir, exist_ok=True)
            open(os.path.join(persist_dir, "docstore.json"), "w").write("dummy")
    class DummyIndex:
        def __init__(self, docs=None):
            self.docs = list(docs or [])
            self.storage_context = DummyStorageContext()
        @classmethod
        def from_documents(cls, docs):
            return cls(docs)
    def load_index_from_storage(storage_context):
        return DummyIndex()
    class DummySettings:
        pass
    core.Document = DummyDocument
    core.VectorStoreIndex = DummyIndex
    core.StorageContext = DummyStorageContext
    core.load_index_from_storage = load_index_from_storage
    core.Settings = DummySettings

    emb = types.ModuleType("llama_index.embeddings.huggingface")
    class HuggingFaceEmbedding:
        def __init__(self, model_name=None, device=None):
            pass
    emb.HuggingFaceEmbedding = HuggingFaceEmbedding

    llms = types.ModuleType("llama_index.llms.ollama")
    class Ollama:
        def __init__(self, model=None, base_url=None):
            pass
    llms.Ollama = Ollama

    monkeypatch.setitem(sys.modules, "llama_index.core", core)
    monkeypatch.setitem(sys.modules, "llama_index.embeddings.huggingface", emb)
    monkeypatch.setitem(sys.modules, "llama_index.llms.ollama", llms)

    return core


def test_get_or_build_semantic_index_build(monkeypatch, tmp_path):
    core = setup_dummy_llama(monkeypatch)
    import importlib
    smi = importlib.import_module("semantic_memory_index")
    monkeypatch.setattr(smi, "INDEX_STORAGE_DIR", str(tmp_path))
    Document = core.Document

    monkeypatch.setattr(smi, "_load_all_reasoning_chains_as_documents", lambda: [Document("a")])
    monkeypatch.setattr(smi, "_load_wikidata_concepts_as_documents", lambda qids: [])
    monkeypatch.setattr(smi, "_load_core_sris_knowledge_as_documents", lambda: [])

    idx = smi.get_or_build_semantic_index(rebuild=False)
    assert idx is not None
    assert os.path.exists(tmp_path / "docstore.json")


def test_get_or_build_semantic_index_load(monkeypatch, tmp_path):
    core = setup_dummy_llama(monkeypatch)
    import importlib
    smi = importlib.import_module("semantic_memory_index")
    monkeypatch.setattr(smi, "INDEX_STORAGE_DIR", str(tmp_path))
    os.makedirs(tmp_path, exist_ok=True)
    (tmp_path / "docstore.json").write_text("dummy")

    monkeypatch.setattr(smi, "load_index_from_storage", lambda sc: core.VectorStoreIndex())

    idx = smi.get_or_build_semantic_index(rebuild=False)
    assert isinstance(idx, core.VectorStoreIndex)
