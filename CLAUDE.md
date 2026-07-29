# CLAUDE.md

Before writing AssemblyAI code, always read:
- https://www.assemblyai.com/docs/agent-instructions.md — rules of the road, operating gotchas
- https://www.assemblyai.com/docs/llms.txt — documentation index

For deeper lookups on specific pages, fetch `https://www.assemblyai.com/docs/llms-full.txt?lang=python`.

The API has changed recently — do NOT rely on memorized parameter names. In particular:
- Universal-3.5 Pro Streaming is the target streaming model. Use `speech_model: "universal-3-5-pro"` unless docs say otherwise; verify against llms-full.txt first.
- Auth header is the raw API key, NO `Bearer` prefix.
- Always terminate streaming sessions explicitly (abandoned WS keeps charging until 3-hour cap).
- Prefer the official `assemblyai` Python SDK over hand-rolled WebSocket code — the SDK handles session lifecycle correctly.
- `voice_focus` values are `"near-field"` / `"far-field"` (hyphenated), not underscored.
- Turn events carry the detected language as `language_code` (singular), not `detected_language`.
- `language_codes` (plural, connection param) biases detection toward a list of languages — distinct from the `language_detection` boolean.

## Project-specific notes

- This is a demo for a translation device (iTranslate). Simulates device client code.
- Pipeline: mic → AssemblyAI streaming STT (auto language detection) → DeepL translation → ElevenLabs TTS → playback.
- **Two-way bilingual mode**: two configured languages (default: English + Hindi). Detected source language determines translation target (the other language). No manual toggle.
- Config values (API keys, language pair, voice IDs) come from .env.
- Keep it a single file (`itranslate.py`) for demo readability. No premature abstraction.
