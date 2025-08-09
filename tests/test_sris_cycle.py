import os, sys, types

# Provide dummy llama_index modules to satisfy imports
llama_index_core = types.ModuleType("llama_index.core")
llama_index_core.Document = object
class DummyIndex:
    def as_retriever(self, *a, **k):
        class R:
            def retrieve(self, *a, **k):
                return []
        return R()
    def insert(self, *a, **k):
        pass
    storage_context = type("SC", (), {"persist": lambda *a, **k: None})()
llama_index_core.VectorStoreIndex = DummyIndex
llama_index_core.StorageContext = type("SC", (), {"from_defaults": lambda *a, **k: None})
llama_index_core.load_index_from_storage = lambda *a, **k: DummyIndex()
llama_index_core.Settings = type("Settings", (), {})

sys.modules.setdefault("llama_index", types.ModuleType("llama_index"))
sys.modules["llama_index.core"] = llama_index_core
sys.modules["llama_index.embeddings"] = types.ModuleType("llama_index.embeddings")
hf_mod = types.ModuleType("llama_index.embeddings.huggingface")
hf_mod.HuggingFaceEmbedding = object
sys.modules["llama_index.embeddings.huggingface"] = hf_mod
sys.modules["llama_index.llms"] = types.ModuleType("llama_index.llms")
ollama_mod = types.ModuleType("llama_index.llms.ollama")
ollama_mod.Ollama = object
sys.modules["llama_index.llms.ollama"] = ollama_mod

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sris_kernel


def test_run_sris_cycle_fast_path(monkeypatch):
    def fake_analyze_perception(text):
        return {
            "user_query_type": "social_greeting",
            "summary": "User greets",
            "language_detected": "en",
            "sentiment": "positive"
        }

    monkeypatch.setattr(sris_kernel, "analyze_perception", fake_analyze_perception)
    sris_kernel.initial_semantic_index = None
    result = sris_kernel.run_sris_cycle({"text": "Hello"})
    assert result["status"] == "ok"
    chain = result["full_reasoning_chain"]
    assert chain["communication_intent"]["intent_type"] == "reciprocate_social_interaction"
