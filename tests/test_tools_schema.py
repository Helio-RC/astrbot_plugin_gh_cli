from core.tool_schemas import TOOL_SCHEMAS


def test_eight_tools():
    assert set(TOOL_SCHEMAS) == {
        "gh_repo",
        "gh_issue",
        "gh_pr",
        "gh_release",
        "gh_gist",
        "gh_search",
        "gh_run",
        "gh_api",
    }


def test_each_schema_has_action_enum():
    for schema in TOOL_SCHEMAS.values():
        assert "properties" in schema["parameters"]
        assert "action" in schema["parameters"]["properties"]
        assert "enum" in schema["parameters"]["properties"]["action"]


def test_each_schema_has_audit_identity_params():
    for schema in TOOL_SCHEMAS.values():
        props = schema["parameters"]["properties"]
        assert "sender_name" in props
        assert "umo" in props
