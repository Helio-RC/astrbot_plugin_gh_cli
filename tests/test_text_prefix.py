"""Tests for the long-text prefix feature."""

import pytest

from core.text_prefix import apply_prefix, render_prefix


def test_render_all_placeholders():
    out = render_prefix("🤖 {datetime} {date} {time} {sender}", sender="Alice")
    assert out.startswith("🤖 ")
    assert out.endswith(" Alice")
    assert (
        "{datetime}" not in out
        and "{date}" not in out
        and "{time}" not in out
        and "{sender}" not in out
    )


def test_render_sender_empty():
    out = render_prefix("by {sender}", sender="")
    assert out == "by "


def test_render_unknown_placeholder_preserved():
    out = render_prefix("a {unknown} b", sender="")
    assert out == "a {unknown} b"


def test_render_empty_template():
    assert render_prefix("", sender="x") == ""


def test_render_date_time_formats():
    out = render_prefix("{date}|{time}", sender="")
    date_part, time_part = out.split("|")
    assert len(date_part) == 10  # YYYY-MM-DD
    assert len(time_part) == 8  # HH:MM:SS


def test_apply_empty_template_returns_body():
    assert apply_prefix("", "hello") == "hello"


def test_apply_prefix_splits_with_blank_line():
    out = apply_prefix("🤖 bot", "hello", sender="")
    assert out == "🤖 bot\n\nhello"


def test_apply_prefix_renders_placeholders():
    out = apply_prefix("by {sender} at {time}", "body", sender="Bob")
    assert out.startswith("by Bob at ")
    assert out.endswith("\n\nbody")


def test_apply_prefix_empty_body_returns_prefix_only():
    out = apply_prefix("prefix", "", sender="")
    assert out == "prefix"


def test_apply_prefix_strips_body_leading_whitespace():
    out = apply_prefix("prefix", "  \nhello", sender="")
    assert out == "prefix\n\nhello"


def test_render_none_template_returns_empty():
    assert render_prefix(None, sender="") == ""


def test_render_non_string_template_raises():
    with pytest.raises(AttributeError):
        render_prefix(123, sender="")
