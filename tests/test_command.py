import pytest

from core.command import build_help, parse_args, parse_command


def test_parse_args_positional_and_flags():
    p = parse_args(["octocat/Hello-World", "-R", "a/b", "--state", "open"])
    assert p["pos"] == ["octocat/Hello-World"]
    assert p["repo"] == "a/b"
    assert p["state"] == "open"


def test_parse_args_equals_form():
    p = parse_args(["--title=hi", "--private"])
    assert p["title"] == "hi"
    assert p["private"] is True


def test_parse_args_bool_flag_equals_false():
    p = parse_args(["--private=false"])
    assert p["private"] is False


def test_parse_args_bool_flag_equals_true():
    p = parse_args(["--private=true"])
    assert p["private"] is True


def test_parse_args_bool_flag_equals_variants():
    p = parse_args(["--private=1", "--draft=on", "--prerelease=yes", "--public=0"])
    assert p["private"] is True
    assert p["draft"] is True
    assert p["prerelease"] is True
    assert p["public"] is False


def test_parse_args_non_bool_equals_stays_string():
    p = parse_args(["--title=hi"])
    assert p["title"] == "hi"


def test_parse_args_missing_value_raises():
    with pytest.raises(ValueError):
        parse_args(["--title"])


def test_parse_command():
    group, action, params = parse_command("issue list -R o/r --state all")
    assert group == "issue"
    assert action == "list"
    assert params["repo"] == "o/r"
    assert params["state"] == "all"


def test_parse_command_no_action():
    group, action, params = parse_command("repo")
    assert group == "repo"
    assert action == ""
    assert params["pos"] == []


def test_build_help_contains_groups():
    help_text = build_help()
    assert "issue" in help_text and "gh_api" not in help_text
