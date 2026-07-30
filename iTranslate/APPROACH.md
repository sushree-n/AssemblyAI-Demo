# iTranslate: Improving STT Accuracy — Approach

## TL;DR

- **Recommendation:** AssemblyAI Universal-3.5 Pro Streaming, with `language_detection` + `language_codes` for bilingual auto-routing, `voice_focus: near-field` for handheld noise suppression, and `mode: max_accuracy` tuned for conversational (not IVR-speed) turn-taking.
- **Top 3 accuracy wins:** (1) native mid-sentence code-switching across 18 languages instead of a fixed source-language toggle, (2) server-side noise suppression tuned for close-talking handheld mics, (3) keyterms/prompting to boost accuracy on travel, medical, or brand-specific vocabulary without retraining anything.
- **Cost:** $0.45/hr ($0.0075/min) of session time for Universal-3.5 Pro Streaming — billed on WebSocket-open duration, not audio sent; see [Cost model](#cost-model).

## What we heard from iTranslate

iTranslate's handheld device currently does STT → translate → TTS entirely to enable conversation between two people who don't share a language. The device itself has no GPU and no meaningful on-device compute — it's WiFi/cellular-connected and depends entirely on cloud APIs. The ask is specifically to **improve STT accuracy**, and the team building this is Python/TypeScript.

The two STT accuracy pressure points implied by the product itself:
1. **Bilingual, code-switching conversations.** Two people speaking different languages means the device has to correctly identify who's speaking which language, turn by turn, without the user manually flipping a switch.
2. **Real-world handheld conditions.** Close-talking mic, but used in noisy real-world environments (streets, restaurants, transit) — not a quiet studio.

## Recommended architecture

```
[Handheld mic] → [Streaming STT: AssemblyAI Universal-3.5 Pro] → [Translate: DeepL]
                                                                        │
[Handheld speaker] ← [TTS: ElevenLabs] ←───────────────────────────────┘
```

The device streams raw audio over WiFi/cellular to AssemblyAI's streaming WebSocket. On each finalized turn, the device (or a thin backend proxying for it) reads the detected language, translates to the other configured language, synthesizes speech, and plays it back — pausing the mic during playback so the device doesn't transcribe its own output.

**Why cloud STT is non-negotiable here:** the device has no GPU and insufficient compute for on-device inference (stated constraint). A model like Universal-3.5 Pro that delivers premium accuracy with native 18-language code-switching is not something that runs on handheld-class hardware — this has to be a network call, which shapes every other recommendation in this doc (bandwidth, reconnection, latency budget).

## How this improves STT accuracy

| Parameter | Value | Why it improves STT accuracy for iTranslate |
|---|---|---|
| `speech_model` | `universal-3-5-pro` | Flagship streaming model; native mid-sentence code-switching across 18 languages (includes English and Hindi) instead of committing to one language per session |
| `language_detection` | `true` | Each finalized turn reports `language_code` + `language_confidence`, needed for bilingual conversation mode where either speaker can start talking |
| `language_codes` | `["en", "hi"]` (configurable pair) | Biases the model toward the two languages actually in play, reducing misclassification versus leaving detection fully open across all 18 |
| `voice_focus` | `near-field` | Isolates the primary speaker on a handheld device; suppresses background chatter, wind, and traffic noise that would otherwise show up as phantom words |
| `mode` | `max_accuracy` | Conversational UX tolerates the extra ~300ms latency; a wrong transcript (and the wrong translation it causes) is a much worse user experience than a slightly slower one |
| `keyterms_prompt` | domain terms (optional) | Boosts accuracy on proper nouns and domain vocabulary — place names, medical terms, brand names — configurable per deployment context (travel, healthcare, retail) |
| Rolling conversation memory | on by default | The model keeps short context across turns, helping disambiguate short follow-up utterances like "yes" or "how much?" |

**A finding worth knowing about, from actually testing this:** the `language_code` field on a Turn event is reported by a *separate classifier pass* from the transcription itself — AssemblyAI's docs say as much (`language_detection` "only controls reporting and doesn't change how the model transcribes"). In testing, we hit turns where the transcript text was correctly transcribed in Hindi, but the reported `language_code` still said `"en"`. Since our language pair uses two non-overlapping scripts (Latin vs. Devanagari), our reference implementation cross-checks the reported language against the actual script of the transcript text as a more reliable routing signal for this specific pair. That trick doesn't generalize to language pairs sharing a script (e.g. English/Spanish) — those would need to lean on `language_confidence` thresholds and possibly hysteresis (don't flip the routing target on a single low-confidence turn). Worth flagging to iTranslate's engineering team as a real detection-reliability edge case, not a hypothetical one.

We also tested a genuine off-pair edge case: a user speaking Spanish (a language outside the configured en/hi pair) got script-matched to English and force-translated EN→HI. DeepL was robust enough to still produce a sensible translation, but that's incidental, not guaranteed — a production deployment would want an explicit "unrecognized language" fallback path (see [What's next](#whats-next-v2-ideas)) rather than silently mis-routing.

## Deploying on the device

| Constraint | Recommendation |
|---|---|
| No GPU / no on-device compute | Cloud STT is required — confirmed above. Keep the device's job limited to audio capture, playback, and network I/O. |
| Cellular bandwidth | Send audio as Opus (`encoding: opus` or `ogg_opus`) instead of raw 16-bit PCM — roughly 8× less bandwidth for the same audio, which matters a lot on a metered cellular connection. `pcm_mulaw` is also a supported streaming encoding (8-bit companded PCM) if the device's audio pipeline can't produce Opus, but Opus is the better tradeoff where available. |
| Cellular reliability | Streaming sessions bill on **WebSocket-open duration**, not audio sent — an idle-but-open connection still accrues cost. Design for graceful reconnect on a dropped connection (buffer audio locally during the gap, discard if the buffer exceeds a few seconds) rather than leaving zombie sessions open. Always send an explicit termination message on conversation end — an abandoned session bills for the full 3-hour cap. |
| Battery | Keep a single streaming session open for the duration of an active conversation (e.g. the ~5 minutes two people are actually talking), rather than opening/closing a session per utterance. Use on-device VAD (e.g. WebRTC VAD) to suppress *sending audio frames* during silence — saving battery and cellular bandwidth — without tearing down the connection itself. Streaming's rate limit is on **new sessions per minute** (5/min free tier, 100+/min paid), not concurrent connections, so a VAD-gated open/close-per-utterance pattern in a fast back-and-forth conversation risks burning through that limit and hitting `1008: Too many concurrent sessions`. Reopening a socket per utterance also adds reconnect latency and would reset whatever rolling conversation context the session had built up. |
| Real-world noise (street, transit, restaurant) | `voice_focus: near-field`, tuned for close-talking handheld mics specifically (as opposed to `far-field`, meant for conference-room-style distant capture). |

## Reference implementation

See [`itranslate.py`](./itranslate.py) — a single-file Python reference client simulating the device's role: mic capture → AssemblyAI streaming STT (bilingual auto-detection) → DeepL translation, routed by detected language → ElevenLabs TTS → playback, with an echo-loop guard (mic pauses during TTS playback) and per-language voices for a natural two-way conversational feel. Run instructions are in [`README.md`](./README.md).

This is a *reference*, not the production device firmware — it's meant to prove the recommended AssemblyAI configuration and pipeline shape are real and working, so the recommendations above aren't speculative.

The reference is in Python, but every connection parameter used here (`speechModel`, `languageDetection`, `languageCodes`, `voiceFocus`) is exposed identically, camelCased, on AssemblyAI's JavaScript/TypeScript SDK — so iTranslate's frontend or Node.js team can implement this same pipeline shape directly, without needing a Python service in between.

## Cost model

AssemblyAI Universal-3.5 Pro Streaming: **$0.45/hr of session time** ($0.0075/min), billed on how long the WebSocket stays open — not on how much audio is actually sent. This is why the device should open one session per conversation and hold it for that conversation's duration, rather than per utterance: cost scales with conversation-session time either way, and per-utterance sessions would add reconnect overhead and rate-limit risk (see [Deploying on the device](#deploying-on-the-device)) for no cost benefit.

Worked example — a mid-size fleet:
- 10,000 devices
- 5-minute average conversation length
- 3 conversations/device/day

`10,000 × 5 min × 3/day = 150,000 minutes/day = 2,500 hours/day`
`2,500 hrs/day × $0.45/hr = $1,125/day ≈ $33,750/month` for STT (30-day month, no volume discount — AssemblyAI offers volume discounts at this scale; worth a conversation with sales).

## What's next (v2 ideas)

- **Bidirectional with an explicit unrecognized-language fallback.** Right now a third, unconfigured language either gets a warning-and-skip (our reference implementation) or silently mis-routes (the Spanish edge case above). A production version should surface this state to the user ("didn't recognize that language") rather than either extreme.
- **`agent_context` for translation continuity.** This parameter is designed to seed the next transcription pass with an agent's own last spoken reply — repurposed here, the device could feed its own last *translated* output back in as context for the next turn, potentially improving disambiguation of short follow-up utterances the way it's designed to for voice agents.
- **Domain packs via `keyterms_prompt` swap.** Travel, medical, and business vocabulary packs, switchable per deployment context or even per conversation.
- **Consolidate translation onto AssemblyAI's LLM Gateway.** AssemblyAI has an existing pattern for exactly this (real-time translation of final transcripts via their LLM Gateway) — worth evaluating against DeepL for iTranslate specifically: one fewer vendor and API key, at the cost of trading a dedicated translation model for an LLM-based one. Worth an accuracy/latency/cost bake-off before committing either way.
- **Offline fallback with cached common phrases** for a full connectivity loss, not just a brief drop.
- **EU data residency** (`wss://streaming.eu.assemblyai.com/v3/ws`) if iTranslate sells into Europe.
