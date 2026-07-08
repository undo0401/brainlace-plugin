"""Tool schemas for the Brainlace Hermes plugin."""

ROOT_PARAM = {
    "type": "string",
    "description": 'Root path.',
}
NOTES_ROOT_PARAM = {
    "type": "string",
    "description": 'notes root relative to the vault root o….',
}
LIMIT_PARAM = {
    "type": "integer",
    "description": 'Max rows.',
    "minimum": 1,
}
DRY_RUN_PARAM = {
    "type": "boolean",
    "description": 'Preview only.',
    "default": False,
}

BRAINLACE_STATUS = {
    "name": "brainlace_status",
    "description": 'Inspect Brainlace.',
    "parameters": {
        "type": "object",
        "properties": {"root": ROOT_PARAM, "notes_root": NOTES_ROOT_PARAM},
    },
}

BRAINLACE_INDEX = {
    "name": "brainlace_index",
    "description": 'Index notes.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "include_archives": {"type": "boolean", "description": 'Include Archive/.archive folders when i….', "default": False},
            "max_notes": {"type": "integer", "description": "Safety cap for indexed Markdown notes.", "minimum": 1},
        },
    },
}

BRAINLACE_SEARCH = {
    "name": "brainlace_search",
    "description": 'Search notes.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "query": {"type": "string", "description": "Search query."},
            "limit": LIMIT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before searching.", "default": False},
        },
        "required": ["query"],
    },
}

BRAINLACE_RELATED = {
    "name": "brainlace_related",
    "description": 'Find related notes.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "text": {"type": "string", "description": "Text to match against indexed notes."},
            "limit": LIMIT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before matching.", "default": False},
        },
        "required": ["text"],
    },
}

BRAINLACE_CATALOG_SEARCH = {
    "name": "brainlace_catalog_search",
    "description": 'Search note catalog.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "query": {"type": "string", "description": "Search query."},
            "text": {"type": "string", "description": "Alias for query."},
            "task_type": {"type": "string", "description": 'task lens such as planning, implementat….'},
            "limit": LIMIT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before searching.", "default": False},
        },
    },
}

BRAINLACE_DESCRIBE_NOTE = {
    "name": "brainlace_describe_note",
    "description": 'Describe Note.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "path": {"type": "string", "description": 'Root path.'},
            "note": {"type": "string", "description": "Alias for path."},
            "refresh": {"type": "boolean", "description": "Rebuild the index before describing.", "default": False},
        },
    },
}

BRAINLACE_ACTIVE_MEMORY_PREVIEW = {
    "name": "brainlace_active_memory_preview",
    "description": 'Run Active memory preview.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "text": {"type": "string", "description": 'Latest user message or conversation tex….'},
            "query": {"type": "string", "description": "Alias for text."},
            "task_type": {"type": "string", "description": 'task lens such as planning, implementat….'},
            "session_type": {"type": "string", "description": 'Session lane. heartbeat/cron/subagent/b….'},
            "limit": LIMIT_PARAM,
            "candidate_limit": LIMIT_PARAM,
            "min_confidence": {"type": "number", "description": 'Minimum catalog confidence for selected….', "default": 0.65},
            "refresh": {"type": "boolean", "description": 'Preview only.', "default": False},
        },
    },
}

BRAINLACE_ACTIVE_MEMORY_CONTEXT = {
    "name": "brainlace_active_memory_context",
    "description": 'Run Active memory context.',
    "parameters": BRAINLACE_ACTIVE_MEMORY_PREVIEW["parameters"],
}

BRAINLACE_CREATE_NOTE = {
    "name": "brainlace_create_note",
    "description": 'Create Note.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "category": {"type": "string", "description": "Folder/category under notes root."},
            "title": {"type": "string", "description": "Note title."},
            "body": {"type": "string", "description": "Markdown body."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": 'frontmatter tags.'},
            "aliases": {"type": "array", "items": {"type": "string"}, "description": 'frontmatter aliases.'},
            "overwrite": {"type": "boolean", "description": "Overwrite an existing note if present.", "default": False},
            "wire_index": {"type": "boolean", "description": 'Create/update category INDEX.md with a….', "default": True},
        },
        "required": ["category", "title", "body"],
    },
}

BRAINLACE_APPEND_NOTE = {
    "name": "brainlace_append_note",
    "description": 'Append Note.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "path": {"type": "string", "description": 'Root path.'},
            "body": {"type": "string", "description": "Markdown text to append."},
            "heading": {"type": "string", "description": 'heading to create before appended text.'},
        },
        "required": ["path", "body"],
    },
}

BRAINLACE_PATCH_NOTE = {
    "name": "brainlace_patch_note",
    "description": 'Patch Note.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "path": {"type": "string", "description": 'Root path.'},
            "old_string": {"type": "string", "description": 'Text to find. Must be unique unless rep….'},
            "new_string": {"type": "string", "description": 'Replacement text. Empty string deletes….'},
            "replace_all": {"type": "boolean", "description": 'Replace all matches instead of requirin….', "default": False},
            "dry_run": DRY_RUN_PARAM,
        },
        "required": ["path", "old_string", "new_string"],
    },
}

BRAINLACE_MOVE_NOTE = {
    "name": "brainlace_move_note",
    "description": 'Move Note.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "source_path": {"type": "string", "description": 'Root path.'},
            "path": {"type": "string", "description": "Alias for source_path."},
            "dest_path": {"type": "string", "description": 'Root path.'},
            "category": {"type": "string", "description": 'Destination category when dest_path is….'},
            "title": {"type": "string", "description": 'Destination title when dest_path is omi….'},
            "overwrite": {"type": "boolean", "description": "Overwrite destination if present.", "default": False},
            "update_links": {"type": "boolean", "description": 'Rewrite inbound wikilinks that point to….', "default": True},
            "wire_index": {"type": "boolean", "description": 'Add a human-readable row to the destina….', "default": True},
            "dry_run": DRY_RUN_PARAM,
        },
        "required": ["source_path"],
    },
}

BRAINLACE_PLAN_NOTE_UPDATE = {
    "name": "brainlace_plan_note_update",
    "description": 'Plan note update.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "text": {"type": "string", "description": 'Conversation text or note content to pl….'},
            "query": {"type": "string", "description": "Alias for text."},
            "action_hint": {"type": "string", "description": "Preferred action such as append or create."},
            "limit": LIMIT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before planning.", "default": False},
        },
    },
}

BRAINLACE_CHECK_LINKS = {
    "name": "brainlace_check_links",
    "description": 'Check Links.',
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before checking.", "default": False},
            "limit": LIMIT_PARAM,
        },
    },
}
