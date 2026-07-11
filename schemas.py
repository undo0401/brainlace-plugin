"""Tool schemas for the Brainlace Hermes plugin."""

ROOT_PARAM = {"type": "string", "description": "Vault root path."}
NOTES_ROOT_PARAM = {"type": "string", "description": "Notes root relative to the vault root."}
LIMIT_PARAM = {"type": "integer", "description": "Max rows.", "minimum": 1}
REFRESH_PARAM = {"type": "boolean", "description": "Rebuild the index before reading.", "default": False}
DRY_RUN_PARAM = {"type": "boolean", "description": "Preview only.", "default": False}

COMMON_READ_PROPS = {
    "root": ROOT_PARAM,
    "notes_root": NOTES_ROOT_PARAM,
    "refresh": REFRESH_PARAM,
    "limit": LIMIT_PARAM,
}

BRAINLACE_READ = {
    "name": "brainlace_read",
    "description": "Read/search Brainlace notes and catalog metadata.",
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
                    "active_memory_preview",
                    "active_memory_context",
                ],
                "description": "Read action/view.",
                "default": "status",
            },
            "query": {"type": "string", "description": "Search/planning query or alias for text/path."},
            "text": {"type": "string", "description": "Text to match or plan from."},
            "task_type": {"type": "string", "description": "Task lens such as planning or implementation."},
            "session_type": {"type": "string", "description": "Session lane such as heartbeat/cron/subagent."},
            "candidate_limit": LIMIT_PARAM,
            "min_confidence": {"type": "number", "description": "Minimum catalog confidence for selected active-memory cards.", "default": 0.65},
            "path": {"type": "string", "description": "Note path."},
            "note": {"type": "string", "description": "Alias for path."},
            "action_hint": {"type": "string", "description": "Preferred note update action such as append or create."},
        },
    },
}

BRAINLACE_CONTROL = {
    "name": "brainlace_control",
    "description": "Operate Brainlace maintenance/control actions such as indexing.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["index"], "description": "Control action.", "default": "index"},
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "include_archives": {"type": "boolean", "description": "Include Archive/.archive folders when indexing.", "default": False},
            "max_notes": {"type": "integer", "description": "Safety cap for indexed Markdown notes.", "minimum": 1},
        },
    },
}

BRAINLACE_WRITE = {
    "name": "brainlace_write",
    "description": "Create, append, patch, or move Brainlace Markdown notes.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["create_note", "append_note", "patch_note", "move_note"], "description": "Write action."},
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "category": {"type": "string", "description": "Folder/category under notes root."},
            "title": {"type": "string", "description": "Note title."},
            "body": {"type": "string", "description": "Markdown body or text to append."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Frontmatter tags."},
            "aliases": {"type": "array", "items": {"type": "string"}, "description": "Frontmatter aliases."},
            "overwrite": {"type": "boolean", "description": "Overwrite an existing note/destination if present.", "default": False},
            "wire_index": {"type": "boolean", "description": "Create/update category INDEX.md wiring.", "default": True},
            "path": {"type": "string", "description": "Note path; also alias for source_path on move."},
            "heading": {"type": "string", "description": "Heading to create before appended text."},
            "old_string": {"type": "string", "description": "Text to find. Must be unique unless replace_all=true."},
            "new_string": {"type": "string", "description": "Replacement text. Empty string deletes."},
            "replace_all": {"type": "boolean", "description": "Replace all matches instead of requiring uniqueness.", "default": False},
            "source_path": {"type": "string", "description": "Move source note path."},
            "dest_path": {"type": "string", "description": "Move destination path."},
            "update_links": {"type": "boolean", "description": "Rewrite inbound wikilinks that point to the moved note.", "default": True},
            "dry_run": DRY_RUN_PARAM,
        },
        "required": ["action"],
    },
}
