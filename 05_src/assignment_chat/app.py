"""
Lot Research — Gradio interface
Viewport-filling chat height, balanced bubble padding, wide column.
"""

import gradio as gr
from dotenv import load_dotenv

from main import lot_research_chat
from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv(".secrets")
load_dotenv(".env")

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

:root {
  --bg: #f7f5f0;
  --bg-s: #ffffff;
  --tint-user: #efe8dc;
  --tint-bot: #f3efe8;
  --b1: rgba(60,45,20,.07);
  --b2: rgba(60,45,20,.12);
  --t1: #1f1a14;
  --t2: #5c5248;
  --t3: #8a8074;
  --ac: #a8763f;
  --ac-s: rgba(168,118,63,.11);
  --cbr: rgba(168,118,63,.32);
  --ct: #7a5228;
}

html, body {
  height: 100% !important;
  margin: 0 !important;
  background: var(--bg) !important;
  overflow: hidden !important;
}

.gradio-container {
  max-width: min(1180px, 97vw) !important;
  width: 100% !important;
  margin: 0 auto !important;
  padding: 0 !important;
  height: 100vh !important;
  height: 100dvh !important;
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
  background: var(--bg) !important;
  color: var(--t1) !important;
  display: flex !important;
  flex-direction: column !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
}

.main, .contain {
  background: var(--bg) !important;
  flex: 1 1 auto !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  overflow: hidden !important;
}

/* Header — aligned with exact 36px side gutters */
.nl-header {
  padding: 12px 36px 6px !important;
  margin: 0 !important;
  flex-shrink: 0 !important;
  box-sizing: border-box !important;
}
.nl-eyebrow {
  font-size: 9.5px !important;
  font-weight: 700 !important;
  letter-spacing: 0.09em !important;
  text-transform: uppercase !important;
  color: var(--t3) !important;
  margin-bottom: 2px !important;
}
.nl-header h1 {
  font-family: 'DM Serif Display', Georgia, serif !important;
  font-size: 20px !important;
  font-weight: 400 !important;
  letter-spacing: -0.02em;
  color: var(--t1) !important;
  margin: 0 0 1px 0 !important;
  line-height: 1.15 !important;
}
.nl-header p {
  font-size: 11.5px !important;
  color: var(--t2) !important;
  margin: 0 !important;
  line-height: 1.25 !important;
}

/* ── Chat panel (Maximized vertical height) ── */
.chatbot,
[data-testid="chatbot"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  flex: 1 1 auto !important;
  min-height: 0 !important;
  max-height: none !important;
  margin: 0 !important;
  padding: 2px 0 !important;
  box-sizing: border-box !important;
}

/* Unified 36px side gutter on message lists */
.chatbot > div,
[data-testid="chatbot"] > div,
.message-wrap,
.message-row {
  padding-left: 36px !important;
  padding-right: 36px !important;
  box-sizing: border-box !important;
}

.chatbot .message,
.message-wrap,
.bubble-wrap,
.message {
  font-size: 14px !important;
  line-height: 1.5 !important;
  font-family: 'Inter', system-ui, sans-serif !important;
  box-shadow: none !important;
  outline: none !important;
}

.chatbot .message,
.chatbot .message *,
.message.user, .message.bot, .message.assistant,
[data-testid="user"], [data-testid="bot"],
.user, .bot, .assistant {
  box-shadow: none !important;
  outline: none !important;
}

/* ── Bubbles & Natural Spacing ── */
.message.user,
.user,
[data-testid="user"],
div.user,
.message.bot,
.message.assistant,
.bot,
.assistant,
[data-testid="bot"],
div.bot {
  border: none !important;
  color: var(--t1) !important;
  padding: 7px 14px !important;
  line-height: 1.5 !important;
  box-sizing: border-box !important;
}

.message.user,
.user,
[data-testid="user"],
div.user {
  background: var(--tint-user) !important;
  border-radius: 12px 12px 4px 12px !important;
  margin: 6px 0 6px auto !important;
  max-width: min(85%, 680px) !important;
}

.message.bot,
.message.assistant,
.bot,
.assistant,
[data-testid="bot"],
div.bot {
  background: var(--tint-bot) !important;
  border-radius: 4px 12px 12px 12px !important;
  margin: 6px 0 6px 0 !important;
  max-width: min(90%, 740px) !important;
}

/* Eliminate awkward inner padding gaps inside Gradio chat bubbles */
.message.user > div,
.message.bot > div,
.message.assistant > div,
[data-testid="user"] > div,
[data-testid="bot"] > div,
.message-content {
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  background: transparent !important;
}

.chatbot > div,
.message-row,
.message-wrap {
  gap: 2px !important;
  margin: 0 !important;
  border: none !important;
  background: transparent !important;
}

/* ── Input & Footer block ── */
.input-container,
form,
.input-row {
  margin: 0 !important;
  padding: 4px 36px 4px 36px !important;
  gap: 8px !important;
  flex-shrink: 0 !important;
  box-sizing: border-box !important;
}

.block, .form, .pending, .wrap {
  margin-bottom: 0 !important;
}

textarea,
input[type="text"] {
  background: var(--bg-s) !important;
  border: 1px solid var(--b2) !important;
  border-radius: 12px !important;
  color: var(--t1) !important;
  font-size: 13.5px !important;
  font-family: 'Inter', system-ui, sans-serif !important;
  padding: 8px 12px !important;
  line-height: 1.35 !important;
  min-height: 38px !important;
  max-height: 90px !important;
  box-shadow: none !important;
}
textarea:focus,
input[type="text"]:focus {
  border-color: var(--ac) !important;
  box-shadow: 0 0 0 3px var(--ac-s) !important;
  outline: none !important;
}

button.primary,
.primary,
button[variant="primary"] {
  background: var(--ac-s) !important;
  border: 1px solid var(--cbr) !important;
  color: var(--ct) !important;
  border-radius: 10px !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  padding: 6px 12px !important;
  min-height: 38px !important;
}
button.primary:hover {
  background: rgba(168,118,63,.18) !important;
}
button.secondary,
.secondary {
  background: transparent !important;
  border: 1px solid var(--b2) !important;
  color: var(--t2) !important;
  border-radius: 10px !important;
  font-size: 11.5px !important;
  padding: 5px 8px !important;
}

.examples {
  margin: 2px 0 0 0 !important;
  padding: 0 36px !important;
  flex-shrink: 0 !important;
  box-sizing: border-box !important;
}
.examples button,
.example {
  background: var(--bg-s) !important;
  border: 1px solid var(--b1) !important;
  border-radius: 999px !important;
  color: var(--t2) !important;
  font-size: 11.5px !important;
  padding: 4px 10px !important;
}
.examples button:hover {
  border-color: var(--cbr) !important;
  color: var(--ct) !important;
  background: var(--ac-s) !important;
}

table {
  border-collapse: collapse !important;
  width: 100% !important;
  font-size: 13px !important;
  margin: 6px 0 8px !important;
}
th, td {
  border: 1px solid var(--b2) !important;
  padding: 5px 8px !important;
  text-align: left !important;
}
th {
  background: var(--tint-user) !important;
  font-weight: 600 !important;
  font-size: 10.5px !important;
  letter-spacing: 0.03em !important;
  text-transform: uppercase !important;
  color: var(--t2) !important;
}

footer, .footer {
  display: none !important;
}

.nl-meta {
  font-size: 9.5px !important;
  color: var(--t3) !important;
  margin: 2px 0 6px 0 !important;
  text-align: center;
  line-height: 1.2 !important;
  flex-shrink: 0 !important;
  padding: 0 36px !important;
  box-sizing: border-box !important;
}
"""


def build_ui():
    with gr.Blocks(
        title="Lot Research",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="stone",
            neutral_hue="stone",
            font=["Inter", "system-ui", "sans-serif"],
        ),
    ) as demo:
        gr.HTML(
            """
            <div class="nl-header">
              <div class="nl-eyebrow">Research desk</div>
              <h1>Lot Research</h1>
              <p>Live crypto &amp; FX · market microstructure · quantitative concepts</p>
            </div>
            """
        )

        gr.ChatInterface(
            fn=lot_research_chat,
            examples=[
                "What is the current price of Bitcoin and Ethereum?",
                "USD to HKD and EUR reference rates",
                "Explain market impact for large orders",
                "What is volatility clustering?",
                "Global crypto market snapshot",
            ],
        )

        gr.HTML(
            '<p class="nl-meta">Indicative data only · not investment advice · restricted topics are refused</p>'
        )

    return demo


if __name__ == "__main__":
    _logs.info("Starting Lot Research…")
    demo = build_ui()
    demo.launch()