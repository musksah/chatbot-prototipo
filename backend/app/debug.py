"""
LangGraph Debug Utilities.

Replaces graph.invoke() with graph.stream() to capture step-by-step
execution metadata: nodes visited, tool calls, token usage, and timings.

Controlled by the DEBUG_GRAPH environment variable (default: False).
When disabled, graph.invoke() is used as before with zero overhead.
"""

import os
import time
import logging
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage

logger = logging.getLogger(__name__)

DEBUG_GRAPH = os.getenv("DEBUG_GRAPH", "false").lower() in ("true", "1", "yes")


def _extract_step_metadata(node_name: str, node_output: dict) -> dict:
    """Extract debug metadata from a single stream step."""
    step_info = {
        "node": node_name,
        "tool_calls": [],
        "token_usage": None,
        "messages_delta": 0,
    }

    messages = node_output.get("messages", [])
    if isinstance(messages, list):
        step_info["messages_delta"] = len(messages)

        for msg in messages:
            # Extract tool calls from AI messages
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    step_info["tool_calls"].append({
                        "name": tc["name"],
                        "args": tc.get("args", {}),
                    })

                # Extract token usage from the AI message
                from .agent import _extract_token_usage
                usage = _extract_token_usage(msg)
                if usage.get("prompt_tokens") or usage.get("completion_tokens"):
                    step_info["token_usage"] = {
                        "input": usage.get("prompt_tokens") or 0,
                        "output": usage.get("completion_tokens") or 0,
                    }

            # Extract tool results
            if isinstance(msg, ToolMessage):
                content_preview = str(msg.content)[:200] if msg.content else ""
                step_info["tool_result_preview"] = content_preview

    return step_info


def _log_step(step_number: int, step_info: dict, duration_ms: int) -> None:
    """Log a single graph step with formatted output."""
    node = step_info["node"]
    tool_calls = step_info["tool_calls"]
    token_usage = step_info["token_usage"]
    msgs = step_info["messages_delta"]

    parts = [f"🔍 Step {step_number}: [{node}]"]
    parts.append(f"⏱️{duration_ms}ms")
    parts.append(f"msgs_delta={msgs}")

    if tool_calls:
        tool_names = ", ".join(tc["name"] for tc in tool_calls)
        parts.append(f"tools=[{tool_names}]")

    if token_usage:
        parts.append(f"tokens(in={token_usage['input']}, out={token_usage['output']})")

    logger.info(" | ".join(parts))


def _log_summary(steps: list, total_ms: int, final_state: dict) -> None:
    """Log a summary of the entire graph execution."""
    nodes_visited = [s["node"] for s in steps]
    total_tool_calls = sum(len(s.get("tool_calls", [])) for s in steps)
    total_tokens_in = sum((s.get("token_usage") or {}).get("input", 0) for s in steps)
    total_tokens_out = sum((s.get("token_usage") or {}).get("output", 0) for s in steps)

    dialog_state = final_state.get("dialog_state", [])
    context = final_state.get("context", {})
    has_summary = bool(context.get("summary"))

    logger.info("━" * 60)
    logger.info("📊 GRAPH EXECUTION SUMMARY")
    logger.info(f"   Total time:    {total_ms}ms")
    logger.info(f"   Steps:         {len(steps)}")
    logger.info(f"   Path:          {' → '.join(nodes_visited)}")
    logger.info(f"   Tool calls:    {total_tool_calls}")
    logger.info(f"   Tokens:        in={total_tokens_in}, out={total_tokens_out}, total={total_tokens_in + total_tokens_out}")
    logger.info(f"   Dialog state:  {dialog_state}")
    logger.info(f"   Has summary:   {has_summary}")
    logger.info("━" * 60)


def stream_graph_with_debug(
    graph,
    inputs: dict,
    config: dict,
) -> dict:
    """
    Execute the LangGraph with step-by-step debug logging.

    When DEBUG_GRAPH=true, uses graph.stream() to capture metadata from
    every node execution. When disabled, falls back to graph.invoke().

    Args:
        graph: Compiled LangGraph with checkpointer.
        inputs: Input dict with messages.
        config: Config dict with thread_id.

    Returns:
        The final state dict (same as graph.invoke() would return).
    """
    if not DEBUG_GRAPH:
        return graph.invoke(inputs, config=config)

    thread_id = config.get("configurable", {}).get("thread_id", "unknown")
    logger.info(f"🐛 [DEBUG] Starting graph stream for thread={thread_id}")

    steps = []
    step_number = 0
    t_total_start = time.monotonic()

    for chunk in graph.stream(inputs, config=config, stream_mode="updates"):
        # LangGraph >=0.2 yields dicts {"node_name": output}, not tuples
        if isinstance(chunk, tuple):
            node_name, node_output = chunk
        elif isinstance(chunk, dict):
            node_name = next(iter(chunk))
            node_output = chunk[node_name]
        else:
            logger.warning(f"[DEBUG] Unexpected stream chunk type: {type(chunk)}")
            continue

        # Some nodes (e.g. summarize) may return None or an empty dict
        # when they have nothing to do.  Skip them to avoid AttributeError
        # ("'NoneType' object has no attribute 'get'") in _extract_step_metadata.
        if not node_output:
            logger.info(f"🔍 Step (skipped): [{node_name}] returned empty/None output")
            continue

        step_number += 1
        t_step_start = time.monotonic()

        step_info = _extract_step_metadata(node_name, node_output)
        step_duration = int((time.monotonic() - t_step_start) * 1000)

        # The step duration here is just metadata extraction time.
        # The actual node execution time is the gap between yields.
        # We measure total time at the end instead.
        steps.append(step_info)
        _log_step(step_number, step_info, step_duration)

    total_ms = int((time.monotonic() - t_total_start) * 1000)

    # Get the final state from the checkpointer
    final_state_snapshot = graph.get_state(config)
    final_state = (final_state_snapshot.values or {}) if final_state_snapshot else {}

    _log_summary(steps, total_ms, final_state)

    return final_state
