import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vault_write_guard import (  # noqa: E402
    check_write_precondition,
    compute_sha256,
    guarded_write,
    is_path_allowed,
    validate_vault_file_format,
)

ALLOWED = ["Obsidian/05_AI_RETURNS_HASHED_MIRROR", "Obsidian/GOVERNANCE_MESH_SUITE/claude-code"]


def test_path_outside_allowlist_denied():
    assert not is_path_allowed("Obsidian/GOVERNANCE_MESH_SUITE/fable-note.md", ALLOWED)


def test_path_inside_allowlist_allowed_exact_and_nested():
    assert is_path_allowed("Obsidian/05_AI_RETURNS_HASHED_MIRROR", ALLOWED)
    assert is_path_allowed(
        "Obsidian/GOVERNANCE_MESH_SUITE/claude-code/note.md", ALLOWED
    )


def test_allowlist_does_not_match_on_prefix_string_collision():
    # "Obsidian/GOVERNANCE_MESH_SUITE_OLD/x.md" must NOT match the allowed
    # "Obsidian/GOVERNANCE_MESH_SUITE/..." prefix just because it starts
    # with the same characters -- only a real path-segment match counts.
    assert not is_path_allowed(
        "Obsidian/GOVERNANCE_MESH_SUITE_OLD/claude-code/note.md", ALLOWED
    )


def test_empty_allowlist_denies_everything():
    assert not is_path_allowed("Obsidian/anything.md", [])


def test_new_file_write_succeeds_when_nothing_exists_remotely():
    path = "Obsidian/05_AI_RETURNS_HASHED_MIRROR/new-note.md"
    result = check_write_precondition(
        path=path,
        content="# New note",
        allowed_prefixes=ALLOWED,
        current_remote_content=None,
        expected_prior_hash=None,
    )
    assert result.ok, result.reason
    assert not result.conflict
    assert result.new_hash == compute_sha256("# New note")


def test_conflict_when_file_unexpectedly_already_exists():
    # This lane believes the path is new (expected_prior_hash=None) but a
    # concurrent read shows content already there -- must not overwrite.
    path = "Obsidian/05_AI_RETURNS_HASHED_MIRROR/new-note.md"
    result = check_write_precondition(
        path=path,
        content="# New note",
        allowed_prefixes=ALLOWED,
        current_remote_content="# Someone else's note",
        expected_prior_hash=None,
    )
    assert not result.ok
    assert result.conflict
    assert result.prior_remote_hash == compute_sha256("# Someone else's note")


def test_conflict_when_remote_content_changed_since_last_read():
    path = "Obsidian/05_AI_RETURNS_HASHED_MIRROR/existing-note.md"
    original = "# Original content"
    result = check_write_precondition(
        path=path,
        content="# My update",
        allowed_prefixes=ALLOWED,
        current_remote_content="# Someone edited this already",
        expected_prior_hash=compute_sha256(original),
    )
    assert not result.ok
    assert result.conflict


def test_update_succeeds_when_remote_content_unchanged():
    path = "Obsidian/05_AI_RETURNS_HASHED_MIRROR/existing-note.md"
    original = "# Original content"
    result = check_write_precondition(
        path=path,
        content="# My update",
        allowed_prefixes=ALLOWED,
        current_remote_content=original,
        expected_prior_hash=compute_sha256(original),
    )
    assert result.ok, result.reason
    assert not result.conflict
    assert result.new_hash == compute_sha256("# My update")


def test_denied_write_reports_reason_and_no_conflict_flag():
    result = check_write_precondition(
        path="Obsidian/GOVERNANCE_MESH_SUITE/fable-note.md",
        content="x",
        allowed_prefixes=ALLOWED,
        current_remote_content=None,
        expected_prior_hash=None,
    )
    assert not result.ok
    assert not result.conflict
    assert "allowlist" in result.reason


def test_valid_canvas_json_passes_format_check():
    valid_canvas = '{"nodes": [], "edges": []}'
    assert validate_vault_file_format("Obsidian/x.canvas", valid_canvas) == []


def test_invalid_canvas_json_fails_format_check():
    errors = validate_vault_file_format("Obsidian/x.canvas", "{not valid json")
    assert errors
    assert "Invalid JSON" in errors[0]


def test_canvas_missing_required_keys_fails_format_check():
    errors = validate_vault_file_format("Obsidian/x.canvas", '{"foo": "bar"}')
    assert errors
    assert "nodes" in errors[0] or "edges" in errors[0]


def test_markdown_files_are_not_subject_to_canvas_check():
    assert validate_vault_file_format("Obsidian/note.md", "not json at all, that's fine") == []


def test_guard_refuses_write_on_bad_canvas_and_never_calls_write_fn():
    calls = []
    result = guarded_write(
        path="Obsidian/05_AI_RETURNS_HASHED_MIRROR/broken.canvas",
        content="{not valid json",
        allowed_prefixes=ALLOWED,
        read_fn=lambda p: None,
        write_fn=lambda p, c: calls.append((p, c)),
    )
    assert not result.ok
    assert calls == []


def test_guard_refuses_write_on_path_denied_and_never_calls_write_fn():
    calls = []
    result = guarded_write(
        path="Obsidian/GOVERNANCE_MESH_SUITE/fable-note.md",
        content="x",
        allowed_prefixes=ALLOWED,
        read_fn=lambda p: None,
        write_fn=lambda p, c: calls.append((p, c)),
    )
    assert not result.ok
    assert calls == []


def test_guard_refuses_write_on_concurrent_edit_and_never_calls_write_fn():
    calls = []
    original = "# Original"
    result = guarded_write(
        path="Obsidian/05_AI_RETURNS_HASHED_MIRROR/existing-note.md",
        content="# My update",
        allowed_prefixes=ALLOWED,
        read_fn=lambda p: "# Someone else already changed this",
        write_fn=lambda p, c: calls.append((p, c)),
        expected_prior_hash=compute_sha256(original),
    )
    assert not result.ok
    assert result.conflict
    assert calls == []


def test_guard_performs_write_when_preconditions_pass():
    calls = []
    result = guarded_write(
        path="Obsidian/05_AI_RETURNS_HASHED_MIRROR/new-note.md",
        content="# New note",
        allowed_prefixes=ALLOWED,
        read_fn=lambda p: None,
        write_fn=lambda p, c: calls.append((p, c)),
    )
    assert result.ok, result.reason
    assert calls == [("Obsidian/05_AI_RETURNS_HASHED_MIRROR/new-note.md", "# New note")]


def test_guard_read_fn_is_called_with_the_target_path():
    seen_paths = []

    def read_fn(p):
        seen_paths.append(p)
        return None

    guarded_write(
        path="Obsidian/05_AI_RETURNS_HASHED_MIRROR/new-note.md",
        content="x",
        allowed_prefixes=ALLOWED,
        read_fn=read_fn,
        write_fn=lambda p, c: None,
    )
    assert seen_paths == ["Obsidian/05_AI_RETURNS_HASHED_MIRROR/new-note.md"]


def test_isolation_no_network_or_subprocess_imports():
    import ast

    source = (
        Path(__file__).resolve().parents[1].joinpath("vault_write_guard.py").read_text()
    )
    tree = ast.parse(source)
    banned_modules = {"socket", "subprocess", "urllib", "requests", "http", "os"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(banned_modules), imported & banned_modules
