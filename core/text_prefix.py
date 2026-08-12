"""Long-text prefix: prepend a configurable template with placeholders."""

from datetime import datetime

PLACEHOLDERS = ("datetime", "date", "time", "sender")


def render_prefix(template: str, sender: str = "") -> str:
    """Render a prefix template, replacing built-in placeholders.

    Supported placeholders:
      {datetime} -> YYYY-MM-DD HH:MM:SS
      {date}     -> YYYY-MM-DD
      {time}     -> HH:MM:SS
      {sender}   -> the sender name (empty string if not provided)

    Unknown placeholders are preserved as-is.
    """
    if not template:
        return ""
    now = datetime.now().astimezone()
    replacements = {
        "{datetime}": now.strftime("%Y-%m-%d %H:%M:%S"),
        "{date}": now.strftime("%Y-%m-%d"),
        "{time}": now.strftime("%H:%M:%S"),
        "{sender}": sender,
    }
    out = template
    for placeholder, value in replacements.items():
        out = out.replace(placeholder, value)
    return out


def apply_prefix(template: str, body: str, sender: str = "") -> str:
    """Prepend the rendered prefix to body, separated by a blank line.

    Empty template returns body unchanged. Empty body returns the rendered
    prefix alone. The body's leading whitespace is stripped before joining.
    """
    if not template:
        return body
    rendered = render_prefix(template, sender)
    if not body:
        return rendered
    return f"{rendered}\n\n{body.lstrip()}"
