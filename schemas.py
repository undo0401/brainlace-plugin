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
    "description": "Scan Markdown notes and write a Brainlace JSON index for agent-readable retrieval.",
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
    "description": "Search Brainlace Markdown notes by title, path, tags, aliases, headings, and text snippets.",
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
    "description": "Find notes related to a piece of text using lightweight token overlap over the Brainlace index.",
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

BRAINLACE_CREATE_NOTE = {
    "name": "brainlace_create_note",
    "description": "Create one Markdown note under the Brainlace notes root, optionally adding frontmatter and index links.",
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
            "wire_index": {"type": "boolean", "description": "Create/update category INDEX.md with a link to the note.", "default": True},
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

BRAINLACE_CHECK_LINKS = {
    "name": "brainlace_check_links",
    "description": "Check indexed Markdown notes for broken wikilinks and orphan notes.",
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
