# Grid07 AI Assignment

Outputs are stored in outputs.md file.

## LangGraph Node Structure (Phase 2)

The LangGraph pipeline in `langgraph_flow.py` is a 3-node linear flow:

1. `decide_search`: Uses the bot persona to pick a topic and generate a search query (structured output).
2. `web_search`: Calls `mock_searxng_search` to fetch keyword-based headline context.
3. `draft_post`: Uses persona + search context to generate a strong opinionated post, capped at 280 chars, then returns strict JSON fields (`bot_id`, `topic`, `post_content`).

Graph edges are `START -> decide_search -> web_search -> draft_post -> END`.

## Prompt Injection Defense (Phase 3)

In `rag_defense.py`, I used a layered defense:

- **Pattern detector (`detect_injection`)**: Regex-based scoring flags likely prompt-injection text (e.g., "ignore previous instructions", role-switch attempts, prompt-exfiltration cues).
- **System-level hard rules**: The system prompt explicitly treats user/thread text as untrusted data, forbids role/persona changes, and rejects instruction resets.
- **Context-grounded rebuttal**: The model is told to respond to argument claims from RAG context (`parent_post`, recent comments, latest reply), not to follow embedded instructions from the thread.
- **Structured output + bounds**: Response is parsed into a strict schema and trimmed to 280 chars, with detector metadata (`injection_detected`, `injection_confidence`, `malicious_signals`) preserved for observability.
