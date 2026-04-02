"""
Claude AI service.

All Anthropic SDK calls are isolated here — no other module may import
``anthropic`` directly.

Public functions
----------------
extract_signature(texts)  — derive a tone-of-voice signature from brand documents
transform_text(text, signature)  — rewrite text applying a stored signature
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SIGNATURE_KEYS = {"tone", "sentence_rhythm", "formality_level", "forms_of_address", "emotional_appeal"}

_PROMPT_FILE = Path(__file__).parent.parent.parent / "extraction_system_prompt.md"
EXTRACTION_SYSTEM: str = _PROMPT_FILE.read_text(encoding="utf-8")

TRANSFORMATION_SYSTEM = """\
You are a brand voice editor. Rewrite the user's text so it matches the provided
tone-of-voice signature exactly. Preserve the original meaning and all factual content.
Return ONLY the rewritten text — no preamble, no explanation, no quotation marks around it.\
"""


class ClaudeServiceError(Exception):
    """Raised when the Claude API returns an error or an unexpected response."""


def extract_signature(texts: list[str]) -> dict[str, Any]:
    """Analyze brand document texts and return a tone-of-voice signature.

    Parameters
    ----------
    texts:
        A list of extracted plain-text strings from brand documents.

    Returns
    -------
    dict
        A dict with exactly five keys: ``tone``, ``sentence_rhythm``,
        ``formality_level``, ``forms_of_address``, ``emotional_appeal``.

    Raises
    ------
    ClaudeServiceError
        On Anthropic API failure, malformed JSON response, or missing keys.
    """
    combined = "\n\n---\n\n".join(texts)
    prompt = f"Analyze the following brand documents and extract the tone-of-voice signature:\n\n{combined}"

    raw = _call_claude(system=EXTRACTION_SYSTEM, user=prompt)
    raw = _strip_code_fence(raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Claude returned malformed JSON: %s", raw)
        raise ClaudeServiceError(f"Claude returned malformed JSON: {exc}") from exc

    if not isinstance(data, dict):
        logger.error("Claude response is not a JSON object: %s", raw)
        raise ClaudeServiceError("Claude response is not a JSON object.")

    missing = SIGNATURE_KEYS - data.keys()
    if missing:
        logger.error("Claude response missing keys %s: %s", missing, raw)
        raise ClaudeServiceError(f"Claude response is missing required keys: {missing}")

    return {key: data[key] for key in SIGNATURE_KEYS}


def transform_text(text: str, signature: dict[str, Any]) -> str:
    """Rewrite *text* applying the given tone-of-voice *signature*.

    Parameters
    ----------
    text:
        The input text to rewrite.
    signature:
        A tone-of-voice signature dict as returned by :func:`extract_signature`.

    Returns
    -------
    str
        The rewritten text in the brand's voice.

    Raises
    ------
    ClaudeServiceError
        On Anthropic API failure or an empty response.
    """
    signature_block = "\n".join(f"- {key}: {value}" for key, value in signature.items())
    prompt = (
        f"Tone-of-voice signature:\n{signature_block}\n\n"
        f"Text to rewrite:\n{text}"
    )

    result = _call_claude(system=TRANSFORMATION_SYSTEM, user=prompt)
    if not result.strip():
        raise ClaudeServiceError("Claude returned an empty transformation response.")
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_code_fence(text: str) -> str:
    """Remove markdown code fences that Claude sometimes adds despite instructions.

    Handles both ```json ... ``` and ``` ... ``` variants.
    """
    text = text.strip()
    if text.startswith("```"):
        # Drop the opening fence line (e.g. ```json or just ```)
        text = text.split("\n", 1)[-1]
        # Drop the closing fence
        if text.endswith("```"):
            text = text[:-3].rstrip()
    return text.strip()


def _call_claude(system: str, user: str) -> str:
    """Send a single message to Claude and return the text content.

    Raises
    ------
    ClaudeServiceError
        On any Anthropic API exception.
    """
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
    except anthropic.APIError as exc:
        raise ClaudeServiceError(f"Anthropic API error: {exc}") from exc
    except Exception as exc:
        raise ClaudeServiceError(f"Unexpected error calling Claude: {exc}") from exc
