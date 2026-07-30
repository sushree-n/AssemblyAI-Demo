# iTranslate Demo

Part 1 of the take-home ([repo root](../README.md)). A reference implementation of a two-way bilingual conversation pipeline for a handheld translation device: mic → AssemblyAI streaming STT (auto language detection) → DeepL translation → ElevenLabs TTS → playback.

See [APPROACH.md](./APPROACH.md) for the actual deliverable: the customer-facing writeup on architecture, why each AssemblyAI feature was chosen, device deployment constraints, and cost model. The code here exists to prove that writeup isn't speculative.

**[Loom walkthrough](https://www.loom.com/share/e3958f5081954ba4a0395ec3fd9ea448)**

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your AssemblyAI, DeepL, and ElevenLabs API keys, and one ElevenLabs voice ID per configured language.

## Run

```bash
python itranslate.py
```

Speak in either configured language (default English/Hindi); the other party's translated, spoken reply plays back automatically. Ctrl+C to stop.

## Requirements

- Python 3.10+
- A working microphone and speaker

## Files

- [`itranslate.py`](./itranslate.py) — the demo
- [`APPROACH.md`](./APPROACH.md) — the writeup (start here)
- [`CLAUDE.md`](./CLAUDE.md) — project-specific notes for anyone extending this with an AI coding agent
