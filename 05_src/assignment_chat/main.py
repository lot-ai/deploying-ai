"""
Lot Research chat core.
Uses the course API gateway pattern and OpenAI Responses API with function calling.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from prompts import return_instructions_root
from tools.market_api import get_crypto_price, get_fx_rate, get_crypto_global
from tools.semantic import semantic_search
from utils.logger import get_logger

_logs = get_logger(__name__)

# Load secrets from common locations
BASE_DIR = Path(__file__).resolve().parent          # .../assignment_chat
SRC_DIR = BASE_DIR.parent                           # .../05_src
ROOT_DIR = SRC_DIR.parent                           # project root

_candidate_dirs = [
    BASE_DIR,                    # assignment_chat/
    SRC_DIR,                     # 05_src/   ← where you placed .secrets
    ROOT_DIR,                    # repo root
    Path.cwd(),                  # current working directory
]

_loaded = []
for d in _candidate_dirs:
    for name in (".env", ".secrets"):
        p = d / name
        if p.is_file():
            load_dotenv(p, override=True)
            _loaded.append(str(p))

# Also try plain names relative to cwd (covers running from 05_src/)
load_dotenv(".env")
load_dotenv(".secrets", override=True)

USE_GATEWAY = os.getenv("USE_GATEWAY", "TRUE").upper() == "TRUE"
MODEL = os.getenv("MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))


def get_client(use_gateway: bool = USE_GATEWAY) -> OpenAI:
    if use_gateway:
        gateway_key = os.getenv("API_GATEWAY_KEY")
        if not gateway_key:
            checked = _loaded or [str(d / ".secrets") for d in _candidate_dirs]
            raise ValueError(
                "API_GATEWAY_KEY is missing.\n"
                f"Files found/loaded: {checked or 'none'}\n"
                "Put API_GATEWAY_KEY=... inside 05_src/.secrets (or assignment_chat/.secrets).\n"
                "Or set USE_GATEWAY=FALSE and provide OPENAI_API_KEY instead."
            )
        client = OpenAI(
            base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
            api_key="any value",
            default_headers={"x-api-key": gateway_key},
        )
    else:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is missing (USE_GATEWAY=FALSE).")
        client = OpenAI()
    return client


_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = get_client()
    return _client

# ---------------------------------------------------------------------------
# Tool schemas for the Responses API
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "name": "get_crypto_price",
        "description": (
            "Retrieve current cryptocurrency prices and 24-hour percentage changes "
            "from CoinGecko. Use when the user asks for the price of Bitcoin, Ethereum, "
            "Solana, or other crypto assets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ids": {
                    "type": "string",
                    "description": "Comma-separated CoinGecko ids, e.g. 'bitcoin,ethereum,solana'",
                },
                "vs_currencies": {
                    "type": "string",
                    "description": "Quote currency, default 'usd'",
                    "default": "usd",
                },
            },
            "required": ["ids"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_fx_rate",
        "description": (
            "Retrieve latest foreign-exchange reference rates from Frankfurter. "
            "Use for currency conversion questions or FX market context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "base": {
                    "type": "string",
                    "description": "Base currency code, e.g. 'USD', 'EUR', 'HKD'",
                    "default": "USD",
                },
                "symbols": {
                    "type": "string",
                    "description": "Optional comma-separated quote currencies, e.g. 'EUR,GBP,JPY,HKD'",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_crypto_global",
        "description": (
            "Retrieve a high-level global cryptocurrency market snapshot "
            "(total market cap, volume, Bitcoin/Ethereum dominance)."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "semantic_search",
        "description": (
            "Search the internal Lot Research knowledge base for conceptual explanations "
            "of market microstructure, risk measures, quantitative finance topics, "
            "Hang Seng context, etc. Use for 'what is', 'explain', or conceptual questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The natural-language search query",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of passages to retrieve (1-5)",
                    "default": 3,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
]

TOOL_IMPL = {
    "get_crypto_price": get_crypto_price,
    "get_fx_rate": get_fx_rate,
    "get_crypto_global": get_crypto_global,
    "semantic_search": semantic_search,
}


def extract_text_content(content: Any) -> str:
    """Flatten Gradio / multi-part content back to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return "" if content is None else str(content)


def sanitize_history(history: List[Dict]) -> List[Dict]:
    clean = []
    for msg in history:
        role = msg.get("role")
        if role not in ("user", "assistant", "system"):
            continue
        clean.append({"role": role, "content": extract_text_content(msg.get("content"))})
    return clean


def _run_tool_calls(response_output, conversation_input: list) -> list:
    """Execute any function calls present in the model output and append results."""
    for item in response_output:
        if getattr(item, "type", None) != "function_call":
            continue
        name = item.name
        call_id = item.call_id
        try:
            args = json.loads(item.arguments or "{}")
        except json.JSONDecodeError:
            args = {}

        _logs.info(f"Tool call: {name}({args})")
        impl = TOOL_IMPL.get(name)
        if impl is None:
            result = f"Unknown tool: {name}"
        else:
            try:
                result = impl(**args)
            except TypeError as e:
                # tolerate missing optional args
                result = f"Tool argument error: {e}"
            except Exception as e:
                _logs.exception(f"Tool {name} failed")
                result = f"Tool execution failed ({type(e).__name__})."

        conversation_input.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps({"result": result}),
            }
        )
    return conversation_input


def lot_research_chat(message: str, history: List[Dict] = None) -> str:
    """
    Main entry point used by Gradio ChatInterface.
    Maintains short-term memory via the history list.
    """
    if history is None:
        history = []

    _logs.info(f"User: {message[:120]}")

    instructions = return_instructions_root()
    conversation_input = sanitize_history(history) + [
        {"role": "user", "content": message}
    ]

    # First model call (may request tools)
    response = _get_client().responses.create(
        model=MODEL,
        instructions=instructions,
        input=conversation_input,
        tools=TOOLS,
        temperature=0.4,
    )

    # If tools were requested, execute them and call again
    has_tool_calls = any(
        getattr(item, "type", None) == "function_call" for item in response.output
    )
    if has_tool_calls:
        conversation_input = conversation_input + list(response.output)
        conversation_input = _run_tool_calls(response.output, conversation_input)
        response = _get_client().responses.create(
            model=MODEL,
            instructions=instructions,
            input=conversation_input,
            tools=TOOLS,
            temperature=0.4,
        )

    text = response.output_text or ""
    _logs.info(f"Assistant: {text[:120]}...")
    return text
