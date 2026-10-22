"""Send scripted user turns through the LangGraph agent and print routing, tool calls and replies.

Usage (from repo root):
    python -X utf8 .claude/skills/chat-smoke-test/scripts/run_chat.py "Hola" "¿Qué proyectos de vivienda hay?"
"""

import asyncio
import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent import builder


def _text(content) -> str:
    # Gemini may return a list of parts instead of a string.
    if isinstance(content, list):
        return "\n".join(
            p if isinstance(p, str) else p.get("text", "")
            for p in content
            if isinstance(p, str) or isinstance(p, dict)
        )
    return str(content or "")


def _turn_tool_calls(messages: list) -> list[str]:
    """Tool calls made after the last human message (i.e. during this turn)."""
    last_human = max(
        (i for i, m in enumerate(messages) if isinstance(m, HumanMessage)),
        default=-1,
    )
    calls = []
    for m in messages[last_human + 1:]:
        if isinstance(m, AIMessage):
            for tc in m.tool_calls:
                args = ", ".join(f"{k}={v!r}" for k, v in tc.get("args", {}).items())
                calls.append(f"{tc['name']}({args})")
    return calls


async def main(turns: list[str]) -> None:
    graph = builder.compile(checkpointer=MemorySaver())
    thread_id = f"smoke-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"thread={thread_id}\n")

    for n, user_msg in enumerate(turns, 1):
        state = await graph.ainvoke({"messages": [HumanMessage(content=user_msg)]}, config)
        messages = state.get("messages", [])
        dialog_state = state.get("dialog_state") or []
        last = messages[-1] if messages else None
        reply = _text(last.content) if isinstance(last, AIMessage) else f"<no AI reply: {type(last).__name__}>"

        print(f"── Turn {n} ──")
        print(f"user:   {user_msg}")
        print(f"agent:  {dialog_state[-1] if dialog_state else 'primary_assistant'}")
        print(f"tools:  {' -> '.join(_turn_tool_calls(messages)) or '(none)'}")
        print(f"reply:  {reply}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main(sys.argv[1:]))
