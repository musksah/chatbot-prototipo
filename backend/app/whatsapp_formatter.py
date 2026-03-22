"""
WhatsApp message formatter — converts Markdown to WhatsApp-native formatting.

WhatsApp supports:
  *bold*          (single asterisk)
  _italic_        (underscore)
  ~strikethrough~ (tilde)
  ```monospace``` (triple backticks)
  > blockquote
  - bullet lists  (dash)
  1. numbered     (number + dot)

Markdown features NOT supported by WhatsApp:
  **bold**        (double asterisk)
  ## headings     (hashes)
  [text](url)     (link syntax)
  ---             (horizontal rules)
  ![img](url)     (images)
"""
import re


def markdown_to_whatsapp(text: str) -> str:
    """
    Convert Markdown-formatted text to WhatsApp-native formatting.

    This is applied as a safety net before sending messages.
    """
    if not text:
        return text

    # 1. Headings:  ### Title  →  *Title*
    text = re.sub(r"^#{1,6}\s+(.+)$", r"*\1*", text, flags=re.MULTILINE)

    # 2. Bold: **text** or __text__  →  *text*  (WhatsApp single asterisk)
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    text = re.sub(r"__(.+?)__", r"*\1*", text)

    # 3. Markdown links: [text](url)  →  text (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

    # 4. Image links: ![alt](url)  →  remove
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # 5. Horizontal rules: --- or ***  →  remove
    text = re.sub(r"^[\s]*[-*_]{3,}[\s]*$", "", text, flags=re.MULTILINE)

    # 6. Bullet normalization: * item  →  • item  (avoid conflict with bold)
    #    Only when * is at the start of a line followed by a space
    text = re.sub(r"^(\s*)\*\s+", r"\1• ", text, flags=re.MULTILINE)

    # 7. Inline code: `code`  →  ```code```  (WhatsApp monospace)
    #    But skip triple backticks (already WhatsApp format)
    text = re.sub(r"(?<!`)` ([^`]+?) `(?!`)", r"```\1```", text)
    text = re.sub(r"(?<!`)`([^`\n]+?)`(?!`)", r"```\1```", text)

    # 8. Clean up excessive blank lines (more than 2 → 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
