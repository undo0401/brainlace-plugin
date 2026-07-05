from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


def load_plugin():
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("brainlace_plugin_under_test", root / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_index_search_create_append_check_links():
    plugin = load_plugin()
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        notes = vault / "notes"
        notes.mkdir()
        (notes / "INDEX.md").write_text("# Notes\n\n- [[Alpha]]\n", encoding="utf-8")
        (notes / "Alpha.md").write_text("---\ntitle: Alpha\ntags:\n  - test\n---\n# Alpha\n\nBrainlace mesh note. [[Missing]]\n", encoding="utf-8")

        indexed = json.loads(plugin._tool_index({"root": str(vault)}))
        assert indexed["ok"] is True
        assert indexed["note_count"] == 2

        search = json.loads(plugin._tool_search({"root": str(vault), "query": "mesh"}))
        assert search["results"]
        assert search["results"][0]["title"] == "Alpha"

        created = json.loads(plugin._tool_create_note({"root": str(vault), "category": "Ideas", "title": "Beta", "body": "Brainlace bridge."}))
        assert Path(created["path"]).exists()
        assert (notes / "Ideas" / "INDEX.md").exists()

        appended = json.loads(plugin._tool_append_note({"root": str(vault), "path": "notes/Ideas/Beta.md", "heading": "追記", "body": "追加メモ"}))
        assert appended["ok"] is True
        assert "追加メモ" in Path(appended["path"]).read_text(encoding="utf-8")

        checked = json.loads(plugin._tool_check_links({"root": str(vault), "refresh": True}))
        assert checked["broken_link_count"] >= 1
