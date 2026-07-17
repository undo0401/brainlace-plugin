"""Tool schemas for the Brainlace Hermes plugin."""

NOTES_ROOT_PARAM = {"type": "string", "description": "Notes root relative to the vault root."}
LIMIT_PARAM = {"type": "integer", "description": "Max rows.", "minimum": 1}
REFRESH_PARAM = {"type": "boolean", "description": "Reindex before reading."}
DRY_RUN_PARAM = {"type": "boolean", "description": "Preview only."}

COMMON_READ_PROPS = {
    "notes_root": NOTES_ROOT_PARAM,
    "refresh": REFRESH_PARAM,
    "limit": LIMIT_PARAM,
}

BRAINLACE_READ = {
    "name": "brainlace_read",
    "description": "Read notes and catalog data.",
    "parameters": {
        "type": "object",
        "properties": {
            **COMMON_READ_PROPS,
            "view": {
                "type": "string",
                "enum": [
                    "status",
                    "search",
                    "related",
                    "catalog_search",
                    "describe_note",
                    "plan_note_update",
                    "check_links",
                ],
                "description": "Read action/view.",

            },
            "query": {"type": "string", "description": "Query or text/path alias."},
            "text": {"type": "string", "description": "Match/planning text."},
            "task_type": {"type": "string", "description": "Task lens."},
            "path": {"type": "string", "description": "Note path."},
            "action_hint": {"type": "string", "description": "Preferred update action."},
        },
    },
}

BRAINLACE_STATUS = {
    "name": "brainlace_status",
    "description": "Read Brainlace index and note-catalog status.",
    "parameters": {"type": "object", "properties": {**COMMON_READ_PROPS}},
}


BRAINLACE_CONTROL = {
    "name": "brainlace_control",
    "description": "Run maintenance actions such as indexing.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["index"], "description": "Control action."},
            "notes_root": NOTES_ROOT_PARAM,
            "include_archives": {"type": "boolean", "description": "Index archive folders."},
            "max_notes": {"type": "integer", "description": "Indexed note safety cap.", "minimum": 1},
        },
    },
}

BRAINLACE_WRITE = {
    "name": "brainlace_write",
    "description": "Create, append, patch, or move notes.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["create_note", "append_note", "patch_note", "move_note"], "description": "Write action."},
            "notes_root": NOTES_ROOT_PARAM,
            "category": {"type": "string", "description": "Note category."},
            "title": {"type": "string", "description": "Note title."},
            "body": {"type": "string", "description": "Markdown body/append text."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Frontmatter tags."},
            "aliases": {"type": "array", "items": {"type": "string"}, "description": "Frontmatter aliases."},
            "overwrite": {"type": "boolean", "description": "Overwrite existing target."},
            "wire_index": {"type": "boolean", "description": "Update category INDEX.md."},
            "path": {"type": "string", "description": "Note/source path."},
            "heading": {"type": "string", "description": "Append heading."},
            "old_string": {"type": "string", "description": "Text to find. Must be unique unless replace_all=true."},
            "new_string": {"type": "string", "description": "Replacement text. Empty string deletes."},
            "replace_all": {"type": "boolean", "description": "Replace all matches."},
            "source_path": {"type": "string", "description": "Move source note path."},
            "dest_path": {"type": "string", "description": "Move destination path."},
            "update_links": {"type": "boolean", "description": "Rewrite inbound wikilinks."},
            "dry_run": DRY_RUN_PARAM,
        },
        "required": ["action"],
    },
}
