import os
from datetime import datetime, timezone
import semantic_memory_fs


def test_save_and_load_chain(tmp_path, monkeypatch):
    tmp_dir = tmp_path / "memory"
    monkeypatch.setattr(semantic_memory_fs, "SMFS_BASE_DIR", str(tmp_dir))
    os.makedirs(tmp_dir, exist_ok=True)
    data = {"id": "test123", "timestamp": datetime.now(timezone.utc).isoformat(), "data": "value"}
    path = semantic_memory_fs.save_chain_to_fs(data)
    assert path is not None and os.path.exists(path)
    loaded = semantic_memory_fs.load_chain_from_fs("test123")
    assert loaded is not None
    assert loaded["data"] == "value"


def test_load_chain_missing(tmp_path, monkeypatch):
    tmp_dir = tmp_path / "memory2"
    monkeypatch.setattr(semantic_memory_fs, "SMFS_BASE_DIR", str(tmp_dir))
    os.makedirs(tmp_dir, exist_ok=True)
    assert semantic_memory_fs.load_chain_from_fs("nope") is None
