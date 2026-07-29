# iTranslate Demo

A reference implementation of a two-way bilingual conversation pipeline for a handheld translation device: mic → AssemblyAI streaming STT (auto language detection) → DeepL translation → ElevenLabs TTS → playback.

See [APPROACH.md](./APPROACH.md) for the customer-facing writeup on architecture, accuracy recommendations, and cost model.

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

Speak in either configured language (default English/Hindi); the other party's translated, spoken reply plays back automatically.

## Requirements

- Python 3.10+
- A working microphone and speaker
