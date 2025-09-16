from __future__ import annotations

import re
from typing import List


CODE_FENCE_RE = re.compile(r"```[ \t]*([a-zA-Z0-9_+-]+)?\n")


def validate_and_fix_markdown_entities(text: str) -> str:
    """
    Validate and fix common markdown entity issues that cause Telegram parsing errors.
    
    - Ensures all markdown entities (*, _, `) are properly closed
    - Escapes problematic characters that might break parsing
    - Handles nested entities properly
    """
    if not text:
        return text
    
    # Track entity states
    in_bold = False
    in_italic = False
    in_code = False
    in_code_block = False
    
    result = []
    i = 0
    
    while i < len(text):
        char = text[i]
        
        if char == '`':
            if i + 2 < len(text) and text[i:i+3] == '```':
                # Code block marker
                if in_code_block:
                    result.append('```')
                    in_code_block = False
                else:
                    result.append('```')
                    in_code_block = True
                i += 3
                continue
            elif not in_code_block:
                # Inline code
                if in_code:
                    result.append('`')
                    in_code = False
                else:
                    result.append('`')
                    in_code = True
                i += 1
                continue
        
        elif char == '*' and not in_code and not in_code_block:
            # Bold marker
            if in_bold:
                result.append('*')
                in_bold = False
            else:
                result.append('*')
                in_bold = True
            i += 1
            continue
            
        elif char == '_' and not in_code and not in_code_block:
            # Italic marker
            if in_italic:
                result.append('_')
                in_italic = False
            else:
                result.append('_')
                in_italic = True
            i += 1
            continue
        
        else:
            result.append(char)
            i += 1
    
    # Close any unclosed entities
    if in_code:
        result.append('`')
    if in_italic:
        result.append('_')
    if in_bold:
        result.append('*')
    if in_code_block:
        result.append('\n```')
    
    return ''.join(result)


def convert_markdown_to_telegram(text: str) -> str:
    """
    Best-effort conversion of generic Markdown to Telegram Markdown (legacy).

    - Removes language specifiers from triple code fences: ```python -> ```
    - Normalizes fenced code blocks to use backticks, which Telegram accepts in Markdown.
    - Validates and fixes markdown entities to prevent parsing errors.
    - Leaves inline code and basic formatting unchanged.
    """
    if not text:
        return text

    # First, validate and fix markdown entities
    text = validate_and_fix_markdown_entities(text)

    # Normalize triple backticks with language to plain triple backticks
    def _strip_lang(m: re.Match[str]) -> str:
        return "```\n"

    text = CODE_FENCE_RE.sub(_strip_lang, text)

    # Ensure closing fence exists if an opening is present but closing is missing
    opens = text.count("```")
    if opens % 2 == 1:
        text += "\n```"

    return text


def split_for_telegram(text: str, limit: int = 4096) -> List[str]:
    """
    Split a message into chunks that fit Telegram's message length limit.

    Attempts to split on paragraph or line boundaries and keeps code fences balanced
    across chunks by reopening/closing as needed.
    """
    if len(text) <= limit:
        return [text]

    parts: List[str] = []

    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    current: List[str] = []
    current_len = 0
    in_code = False

    def push_current():
        nonlocal current, current_len, in_code
        if not current:
            return
        chunk = "\n\n".join(current)
        # Balance code fences for this chunk
        if in_code and not chunk.endswith("```"):
            chunk += "\n```"
        parts.append(chunk)
        current = []
        current_len = 0

    for para in paragraphs:
        # Track code fence state within the paragraph
        fence_count = para.count("```")

        add = ("\n\n" if current else "") + para
        if current_len + len(add) <= limit:
            current.append(para)
            current_len += len(add)
            if fence_count % 2 == 1:
                in_code = not in_code
            continue

        # Paragraph too big for current chunk — push current and split paragraph further
        push_current()

        # Split paragraph by lines to fit
        lines = para.split("\n")
        buf: List[str] = []
        buf_len = 0
        for line in lines:
            prefix = ("\n" if buf else "")
            candidate = prefix + line
            if buf_len + len(candidate) > limit:
                # finalize previous buffer
                chunk = "\n".join(buf)
                # close code fence if opened in this chunk
                if chunk.count("```") % 2 == 1:
                    chunk += "\n```"
                    in_code = not in_code
                parts.append(chunk)
                buf = [line]
                buf_len = len(line)
            else:
                buf.append(line)
                buf_len += len(candidate)
        if buf:
            chunk = "\n".join(buf)
            if chunk.count("```") % 2 == 1:
                chunk += "\n```"
                in_code = not in_code
            parts.append(chunk)

    push_current()

    # Ensure each part within limit; as a last resort hard-split
    fixed: List[str] = []
    for p in parts:
        if len(p) <= limit:
            fixed.append(p)
            continue
        # hard split preserving limit
        for i in range(0, len(p), limit):
            fixed.append(p[i : i + limit])

    return fixed or [text[:limit]]


def prepare_telegram_messages_from_markdown(text: str, limit: int = 4096) -> List[str]:
    return split_for_telegram(convert_markdown_to_telegram(text), limit)


