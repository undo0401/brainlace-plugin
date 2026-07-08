"""Tool schemas for the Brainlace Hermes plugin."""

ROOT_PARAM = {
    "type": "string",
    "description": "Optional vault root. Defaults to BRAINLACE_VAULT_ROOT, OBSIDIAN_VAULT_PATH, or /opt/data/workspace.",
}
NOTES_ROOT_PARAM = {
    "type": "string",
    "description": "Optional notes root relative to the vault root or absolute. Defaults to notes.",
}
LIMIT_PARAM = {
    "type": "integer",
    "description": "Maximum number of rows to return.",
    "minimum": 1,
}
DRY_RUN_PARAM = {
    "type": "boolean",
    "description": "Preview the edit without writing files.",
    "default": False,
}

BRAINLACE_STATUS = {
    "name": "brainlace_status",
    "description": "Inspect Brainlace vault paths, index freshness, and Markdown note counts.",
    "parameters": {
        "type": "object",
        "properties": {"root": ROOT_PARAM, "notes_root": NOTES_ROOT_PARAM},
    },
}

BRAINLACE_INDEX = {
    "name": "brainlace_index",
    "description": "Scan Markdown notes and write a richer Brainlace JSON index for agent-readable retrieval.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "include_archives": {"type": "boolean", "description": "Include Archive/.archive folders when indexing.", "default": False},
            "max_notes": {"type": "integer", "description": "Safety cap for indexed Markdown notes.", "minimum": 1},
        },
    },
}

BRAINLACE_SEARCH = {
    "name": "brainlace_search",
    "description": "Search Brainlace Markdown notes by title, path, category, tags, aliases, headings, backlinks, and text snippets.",
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
    "description": "Find notes related to a piece of text using weighted title/alias/tag/path/token overlap over the Brainlace index.",
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
    "description": "Search Brainlace notes as catalog cards: role, freshness, source quality, read cost, and why a note is useful before reading the full body.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "query": {"type": "string", "description": "Search query."},
            "text": {"type": "string", "description": "Alias for query."},
            "task_type": {"type": "string", "description": "Optional task lens such as planning, implementation, design, current, or operations."},
            "limit": LIMIT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before searching.", "default": False},
        },
    },
}

BRAINLACE_DESCRIBE_NOTE = {
    "name": "brainlace_describe_note",
    "description": "Describe one Brainlace note as a catalog card without modifying the note: explicit frontmatter, inferred role/freshness/source quality, use cautions, headings, and link context.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "path": {"type": "string", "description": "Note path relative to vault/notes root or an absolute path inside the vault."},
            "note": {"type": "string", "description": "Alias for path."},
            "refresh": {"type": "boolean", "description": "Rebuild the index before describing.", "default": False},
        },
    },
}

BRAINLACE_ACTIVE_MEMORY_PREVIEW = {
    "name": "brainlace_active_memory_preview",
    "description": "Preview which Brainlace catalog cards would be safe and useful as soft active-memory context before a reply. Does not modify notes or prompt state.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "text": {"type": "string", "description": "Latest user message or conversation text to recall notes for."},
            "query": {"type": "string", "description": "Alias for text."},
            "task_type": {"type": "string", "description": "Optional task lens such as planning, implementation, design, current, consultation, or conversation."},
            "session_type": {"type": "string", "description": "Session lane. heartbeat/cron/subagent/background are blocked by default."},
            "limit": LIMIT_PARAM,
            "candidate_limit": LIMIT_PARAM,
            "min_confidence": {"type": "number", "description": "Minimum catalog confidence for selected cards.", "default": 0.65},
            "refresh": {"type": "boolean", "description": "Rebuild the index before previewing.", "default": False},
        },
    },
}

BRAINLACE_ACTIVE_MEMORY_CONTEXT = {
    "name": "brainlace_active_memory_context",
    "description": "Return a compact Brainlace active-memory context packet for a prompt/memory layer to optionally inject. Brainlace only retrieves and formats; it does not modify memory or prompts.",
    "parameters": BRAINLACE_ACTIVE_MEMORY_PREVIEW["parameters"],
}

BRAINLACE_CREATE_NOTE = {
    "name": "brainlace_create_note",
    "description": "Create one Markdown note under the Brainlace notes root, optionally adding frontmatter and human-readable index links.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "category": {"type": "string", "description": "Folder/category under notes root."},
            "title": {"type": "string", "description": "Note title."},
            "body": {"type": "string", "description": "Markdown body."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional frontmatter tags."},
            "aliases": {"type": "array", "items": {"type": "string"}, "description": "Optional frontmatter aliases."},
            "overwrite": {"type": "boolean", "description": "Overwrite an existing note if present.", "default": False},
            "wire_index": {"type": "boolean", "description": "Create/update category INDEX.md with a human-readable link row.", "default": True},
        },
        "required": ["category", "title", "body"],
    },
}

BRAINLACE_APPEND_NOTE = {
    "name": "brainlace_append_note",
    "description": "Append Markdown text to an existing note inside the Brainlace vault boundary.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "path": {"type": "string", "description": "Note path relative to vault/notes root or an absolute path inside the vault."},
            "body": {"type": "string", "description": "Markdown text to append."},
            "heading": {"type": "string", "description": "Optional heading to create before appended text."},
        },
        "required": ["path", "body"],
    },
}

BRAINLACE_PATCH_NOTE = {
    "name": "brainlace_patch_note",
    "description": "Patch an existing Brainlace note with old_string/new_string replacement and return a unified diff.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "path": {"type": "string", "description": "Note path relative to vault/notes root or an absolute path inside the vault."},
            "old_string": {"type": "string", "description": "Text to find. Must be unique unless replace_all=true."},
            "new_string": {"type": "string", "description": "Replacement text. Empty string deletes the match."},
            "replace_all": {"type": "boolean", "description": "Replace all matches instead of requiring uniqueness.", "default": False},
            "dry_run": DRY_RUN_PARAM,
        },
        "required": ["path", "old_string", "new_string"],
    },
}

BRAINLACE_MOVE_NOTE = {
    "name": "brainlace_move_note",
    "description": "Move or rename a Markdown note and optionally update inbound wikilinks and category INDEX.md wiring.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "source_path": {"type": "string", "description": "Existing note path relative to vault/notes root or absolute."},
            "path": {"type": "string", "description": "Alias for source_path."},
            "dest_path": {"type": "string", "description": "Destination path relative to vault/notes root or absolute."},
            "category": {"type": "string", "description": "Destination category when dest_path is omitted."},
            "title": {"type": "string", "description": "Destination title when dest_path is omitted."},
            "overwrite": {"type": "boolean", "description": "Overwrite destination if present.", "default": False},
            "update_links": {"type": "boolean", "description": "Rewrite inbound wikilinks that point to the old note.", "default": True},
            "wire_index": {"type": "boolean", "description": "Add a human-readable row to the destination category INDEX.md.", "default": True},
            "dry_run": DRY_RUN_PARAM,
        },
        "required": ["source_path"],
    },
}

BRAINLACE_PLAN_NOTE_UPDATE = {
    "name": "brainlace_plan_note_update",
    "description": "Plan where a new note update should land by returning likely target notes and a create/append recommendation.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": ROOT_PARAM,
            "notes_root": NOTES_ROOT_PARAM,
            "text": {"type": "string", "description": "Conversation text or note content to place."},
            "query": {"type": "string", "description": "Alias for text."},
            "action_hint": {"type": "string", "description": "Preferred action such as append or create."},
            "limit": LIMIT_PARAM,
            "refresh": {"type": "boolean", "description": "Rebuild the index before planning.", "default": False},
        },
    },
}

BRAINLACE_CHECK_LINKS = {
    "name": "brainlace_check_links",
    "description": "Check indexed Markdown notes for broken wikilinks and orphan notes using Brainlace's path-aware resolver.",
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
