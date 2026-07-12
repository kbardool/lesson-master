"""
Single shared Jinja2Templates instance with all custom filters registered.
Import this in routers instead of creating a new instance per-router.
"""

import markdown as _md
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

templates = Jinja2Templates(directory="app/templates")


def pluralize(count: int, singular: str = "", plural: str = "s") -> str:
    return singular if count == 1 else plural


def render_markdown(text: str) -> Markup:
    """Convert Markdown to safe HTML. Markup tells Jinja2 not to re-escape it."""
    html = _md.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br"],
    )
    return Markup(html)


templates.env.filters["pluralize"] = pluralize
templates.env.filters["markdown"] = render_markdown
