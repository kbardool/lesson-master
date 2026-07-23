"""
AI-assisted exercise generation using the Anthropic API.
Requires ANTHROPIC_API_KEY to be set in the environment.
"""

import json
import os
from dataclasses import dataclass

import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your environment before starting the server."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


@dataclass
class GeneratedExercise:
    title: str
    prompt: str
    starter_code: str | None
    reference_solution: str | None
    difficulty: str


def generate_exercises(
    topic_name: str,
    description: str | None,
    difficulty: str,
    count: int = 3,
) -> list[GeneratedExercise]:
    """
    Call Claude to generate `count` exercises for a topic.
    Returns a list of GeneratedExercise dataclasses.
    Raises ValueError if the API response can't be parsed.
    """
    prompt = f"""Generate {count} practical Python coding exercises for the topic: "{topic_name}".

Topic description: {description or "N/A"}
Overall difficulty level: {difficulty}

Requirements:
- Exercises should be hands-on and require writing real Python code
- Each exercise should be self-contained and clearly specified
- starter_code should give the learner a skeleton to fill in (function signature, docstring, pass)
- reference_solution should be a clean, correct implementation
- Vary difficulty slightly across the set if it makes sense

Return ONLY a JSON array with no preamble, explanation, or markdown fences.
Each object must have exactly these fields:

[
  {{
    "title": "Short action-oriented title",
    "prompt": "Clear description of what to implement, including any constraints or examples",
    "starter_code": "def my_func(...):\\n    pass",
    "reference_solution": "def my_func(...):\\n    # implementation",
    "difficulty": "beginner" | "intermediate" | "advanced"
  }}
]"""

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if the model adds them despite instructions
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON output: {e}\n\nRaw output:\n{raw}") from e

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got: {type(data)}")

    exercises = []
    for item in data:
        exercises.append(
            GeneratedExercise(
                title=item.get("title", "Untitled"),
                prompt=item.get("prompt", ""),
                starter_code=item.get("starter_code") or None,
                reference_solution=item.get("reference_solution") or None,
                difficulty=item.get("difficulty", difficulty),
            )
        )
    return exercises


_LEVEL_GUIDANCE = {
    "basic": (
        "Assume the reader knows basic Python syntax but is new to this topic. "
        "Focus on fundamentals with simple, clear examples. Avoid jargon."
    ),
    "intermediate": (
        "Assume solid Python knowledge. Cover practical patterns, real-world usage, "
        "and edge cases. Include more nuanced examples."
    ),
    "advanced": (
        "Assume expert-level Python knowledge. Cover internals, performance implications, "
        "subtle behaviors, and advanced patterns. Don't shy away from complexity."
    ),
}


def _truncate_to_words(text: str, max_words: int) -> str:
    """Defensively cap `text` at `max_words` words, in case the model overshoots."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",.;:") + "…"


def generate_subject_description(name: str, description: str | None = None) -> str:
    """
    Generate a subject description (<=60 words) from a subject name and an
    optional draft description typed so far. Returns the generated text.
    """
    draft_note = (
        f'\n\nThe user has started writing this draft description — refine and '
        f'build on it rather than ignoring it: "{description}"'
        if description
        else ""
    )
    prompt = f"""Write a description for a learning subject titled "{name}".{draft_note}

Requirements:
- Explain what the subject covers and who it's useful for
- Engaging, professional tone suitable for a curriculum catalog
- No more than 60 words

Return only the description text. No preamble, no quotes, no markdown."""

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    generated = message.content[0].text.strip()
    return _truncate_to_words(generated, 60)


def generate_lesson(
    topic_name: str,
    description: str | None,
    difficulty: str,
    level: str,
) -> str:
    """
    Generate a structured Markdown lesson for a topic at a given level.
    Returns the raw Markdown string.
    """
    guidance = _LEVEL_GUIDANCE.get(level, "")
    prompt = f"""Write a {level}-level Python lesson on: "{topic_name}".

Topic description: {description or "N/A"}
Difficulty context: {difficulty}
Level guidance: {guidance}

Structure the lesson using exactly these Markdown sections:

## Overview
What this topic is and why it matters (2-3 sentences).

## Key Concepts
Core ideas, each explained concisely. Use bullet points.

## Code Examples
2-3 practical, runnable examples. Each must have a brief explanation before the code block.
Use ```python fenced code blocks.

## Common Pitfalls
2-3 specific mistakes people make with this topic and how to avoid them.

## Summary
3-5 bullet points of the most important takeaways.

Return only the Markdown content. No preamble, no "Here is your lesson", just the Markdown."""

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
