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


def test_register_exposes_catalog_tools():
    plugin = load_plugin()

    class FakeCtx:
        def __init__(self):
            self.tools = []
            self.skills = []

        def register_skill(self, *args):
            self.skills.append(args)

        def register_tool(self, **kwargs):
            self.tools.append(kwargs)

    ctx = FakeCtx()
    plugin.register(ctx)
    names = {tool["name"] for tool in ctx.tools}
    assert names == {"brainlace_read", "brainlace_control", "brainlace_write"}
    assert ctx.skills == [
        (
            "brainlace",
            plugin.PLUGIN_DIR / "skills" / "brainlace" / "SKILL.md",
            "Operate Brainlace, LIN's filesystem-first second-brain framework.",
        )
    ]
    for tool in ctx.tools:
        assert "root" not in tool["schema"]["parameters"]["properties"]


def test_index_search_create_append_patch_move_plan_check_links():
    plugin = load_plugin()
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        notes = vault / "notes"
        notes.mkdir()
        (vault / "designs").mkdir()
        (vault / "designs" / "mesh.md").write_text("# Mesh design\n", encoding="utf-8")
        (notes / "INDEX.md").write_text("# Notes\n\n- [[Alpha]]\n", encoding="utf-8")
        (notes / "Alpha.md").write_text(
            "---\ntitle: Alpha\ntags:\n  - test\n---\n# Alpha\n\nBrainlace mesh note. [[Missing]] [[../designs/mesh]]\n",
            encoding="utf-8",
        )

        indexed = json.loads(plugin._tool_index({"root": str(vault)}))
        assert indexed["ok"] is True
        assert indexed["note_count"] == 2
        assert indexed["summary"]["broken_link_count"] == 1

        search = json.loads(plugin._tool_search({"root": str(vault), "query": "Alpha"}))
        assert search["results"]
        assert search["results"][0]["title"] == "Alpha"
        assert "category" in search["results"][0]

        describe = json.loads(plugin._tool_describe_note({"root": str(vault), "path": "Alpha.md"}))
        assert describe["ok"] is True
        assert describe["note"]["title"] == "Alpha"
        assert describe["note"]["frontmatter"]["context_role"] is None
        assert describe["catalog"]["inferred_context_role"] == "design"
        assert describe["catalog"]["freshness_guess"] == "current"
        assert describe["catalog"]["source_quality_guess"] == "interpretation"
        assert "live_system_state" in describe["catalog"]["when_not_to_use"]
        assert describe["catalog"]["confidence"] > 0

        catalog = json.loads(plugin._tool_catalog_search({"root": str(vault), "query": "Brainlace design", "task_type": "planning"}))
        assert catalog["ok"] is True
        assert catalog["results"]
        assert catalog["results"][0]["title"] == "Alpha"
        assert catalog["results"][0]["catalog"]["inferred_context_role"] == "design"
        assert catalog["results"][0]["recommended_action"] == "describe"
        assert catalog["results"][0]["read_cost"] == "summary_only"

        created = json.loads(plugin._tool_create_note({"root": str(vault), "category": "Ideas", "title": "Beta", "body": "Brainlace bridge."}))
        assert Path(created["path"]).exists()
        index_text = (notes / "Ideas" / "INDEX.md").read_text(encoding="utf-8")
        assert "## この階層のノート" in index_text
        assert "Brainlace bridge" in index_text

        appended = json.loads(plugin._tool_append_note({"root": str(vault), "path": "notes/Ideas/Beta.md", "heading": "追記", "body": "追加メモ"}))
        assert appended["ok"] is True
        assert "追加メモ" in Path(appended["path"]).read_text(encoding="utf-8")

        patched = json.loads(plugin._tool_patch_note({"root": str(vault), "path": "Ideas/Beta.md", "old_string": "追加メモ", "new_string": "追加メモ2"}))
        assert patched["ok"] is True
        assert "追加メモ2" in Path(patched["path"]).read_text(encoding="utf-8")
        assert "diff" in patched and "追加メモ2" in patched["diff"]

        (notes / "Gamma.md").write_text("# Gamma\n\nSee [[Beta]].\n", encoding="utf-8")
        moved_preview = json.loads(plugin._tool_move_note({"root": str(vault), "source_path": "Ideas/Beta.md", "category": "Archive", "title": "Beta moved", "dry_run": True}))
        assert moved_preview["dry_run"] is True
        assert moved_preview["updated_link_files"]

        moved = json.loads(plugin._tool_move_note({"root": str(vault), "source_path": "Ideas/Beta.md", "category": "Archive", "title": "Beta moved"}))
        assert moved["ok"] is True
        assert (notes / "Archive" / "Beta moved.md").exists()
        assert "[[Archive/Beta moved|Beta]]" in (notes / "Gamma.md").read_text(encoding="utf-8") or "[[Archive/Beta moved]]" in (notes / "Gamma.md").read_text(encoding="utf-8")

        plan = json.loads(plugin._tool_plan_note_update({"root": str(vault), "text": "Brainlace bridge 追加メモ"}))
        assert plan["ok"] is True
        assert plan["recommendation"]["action"] in {"append", "create"}

        checked = json.loads(plugin._tool_check_links({"root": str(vault), "refresh": True}))
        assert checked["broken_link_count"] == 1
        assert checked["broken_links"][0]["link"] == "Missing"
