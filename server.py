#!/usr/bin/env python3
"""
FastAPI server — connects browser UI to the financial portfolio orchestrator.
Exposes an AG-UI compliant /agent endpoint (SSE event stream) plus a simple
non-streaming /chat fallback.
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import os
import threading
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ag_ui.core import (
    RunAgentInput,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    EventType,
)
from ag_ui.encoder import EventEncoder

from agents.orchestrator import orchestrator
from tools.chart_tools import CHART_STORE

app = FastAPI(title="Financial Portfolio Assistant")

# Mount built frontend assets only when dist/ exists (after npm run build)
if os.path.isdir("dist/assets"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

encoder = EventEncoder()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sse(event) -> str:
    """Serialize an ag_ui event to an SSE data line."""
    return encoder.encode(event) + "\n"


# ── AG-UI endpoint ─────────────────────────────────────────────────────────────

@app.post("/agent")
async def agent_endpoint(request: Request):
    """
    AG-UI compliant endpoint.
    Accepts RunAgentInput JSON, streams AG-UI events back via SSE.
    """
    body = await request.json()
    # Supply defaults for optional AG-UI fields the frontend doesn't send
    body.setdefault("state", None)
    body.setdefault("tools", [])
    body.setdefault("context", [])
    body.setdefault("forwardedProps", {})
    run_input = RunAgentInput.model_validate(body)

    # Extract last user message as the prompt
    user_message = ""
    for msg in reversed(run_input.messages or []):
        role = getattr(msg, "role", None)
        content = getattr(msg, "content", None)
        if role == "user" and content:
            user_message = content
            break

    thread_id = run_input.thread_id or str(uuid.uuid4())
    run_id = run_input.run_id or str(uuid.uuid4())

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    # ── Strands callback handler ──────────────────────────────────────────────
    # Strands calls this for every streaming event from the LLM / tool layer.
    # kwargs keys: data (str token), complete (bool), event (dict), reasoningText

    active_msg_id: list[str] = []          # mutable cell
    active_tool_calls: dict[str, str] = {} # tool_use_id → tool_name

    def callback_handler(**kwargs):
        data: str = kwargs.get("data", "")
        complete: bool = kwargs.get("complete", False)
        raw_event: dict = kwargs.get("event", {}) or {}

        # ── Tool call start ───────────────────────────────────────────────────
        tool_use = (
            raw_event
            .get("contentBlockStart", {})
            .get("start", {})
            .get("toolUse")
        )
        if tool_use:
            tool_id = tool_use.get("toolUseId", str(uuid.uuid4()))
            tool_name = tool_use.get("name", "unknown_tool")
            active_tool_calls[tool_id] = tool_name
            parent_msg = active_msg_id[0] if active_msg_id else None
            loop.call_soon_threadsafe(queue.put_nowait, ("tool_start", tool_id, tool_name, parent_msg))
            return

        # ── Tool call args delta ──────────────────────────────────────────────
        tool_delta = (
            raw_event
            .get("contentBlockDelta", {})
            .get("delta", {})
            .get("toolUse", {})
        )
        if tool_delta:
            # Find which tool is currently active (last opened one)
            if active_tool_calls:
                tool_id = next(reversed(active_tool_calls))
                args_chunk = tool_delta.get("input", "")
                if args_chunk:
                    loop.call_soon_threadsafe(queue.put_nowait, ("tool_args", tool_id, args_chunk))
            return

        # ── Tool call end (contentBlockStop after a toolUse block) ────────────
        if raw_event.get("contentBlockStop") is not None and active_tool_calls:
            tool_id = next(reversed(active_tool_calls))
            active_tool_calls.pop(tool_id, None)
            loop.call_soon_threadsafe(queue.put_nowait, ("tool_end", tool_id))
            return

        # ── Text token ────────────────────────────────────────────────────────
        if data:
            if not active_msg_id:
                msg_id = str(uuid.uuid4())
                active_msg_id.append(msg_id)
                loop.call_soon_threadsafe(queue.put_nowait, ("msg_start", msg_id))
            loop.call_soon_threadsafe(queue.put_nowait, ("token", active_msg_id[0], data))

        if complete and active_msg_id:
            loop.call_soon_threadsafe(queue.put_nowait, ("msg_end", active_msg_id[0]))
            active_msg_id.clear()

    # ── Run agent in background thread ────────────────────────────────────────
    def run_agent():
        try:
            orchestrator(user_message, callback_handler=callback_handler)
            loop.call_soon_threadsafe(queue.put_nowait, ("done",))
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))

    threading.Thread(target=run_agent, daemon=True).start()

    # ── SSE generator ─────────────────────────────────────────────────────────
    async def event_stream():
        yield _sse(RunStartedEvent(thread_id=thread_id, run_id=run_id))

        while True:
            item = await queue.get()
            kind = item[0]

            if kind == "msg_start":
                yield _sse(TextMessageStartEvent(message_id=item[1], role="assistant"))

            elif kind == "token":
                yield _sse(TextMessageContentEvent(message_id=item[1], delta=item[2]))

            elif kind == "msg_end":
                yield _sse(TextMessageEndEvent(message_id=item[1]))

            elif kind == "tool_start":
                _, tool_id, tool_name, parent_msg = item
                yield _sse(ToolCallStartEvent(
                    tool_call_id=tool_id,
                    tool_call_name=tool_name,
                    parent_message_id=parent_msg,
                ))

            elif kind == "tool_args":
                _, tool_id, delta = item
                yield _sse(ToolCallArgsEvent(tool_call_id=tool_id, delta=delta))

            elif kind == "tool_end":
                yield _sse(ToolCallEndEvent(tool_call_id=item[1]))

            elif kind == "done":
                yield _sse(RunFinishedEvent(thread_id=thread_id, run_id=run_id))
                break

            elif kind == "error":
                yield _sse(RunErrorEvent(message=item[1]))
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Simple non-streaming fallback ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, orchestrator, req.message)
    return {"response": str(result)}


# ── Static file serving ───────────────────────────────────────────────────────

@app.get("/")
async def index():
    if os.path.isfile("dist/index.html"):
        return FileResponse("dist/index.html")
    return FileResponse("static/index.html")


@app.get("/chart/{chart_id}")
async def serve_chart(chart_id: str):
    from fastapi.responses import HTMLResponse
    html = CHART_STORE.get(chart_id)
    if html is None:
        raise HTTPException(status_code=404, detail="Chart not found")
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
