# Spanglish Inc. - Internal Engineering Summary

**Status: Not a bug on our side. Client misconfiguration, reproduced and confirmed. No infra action needed.**

## TL;DR

Spanglish's Java client declares `encoding=opus` in the streaming WebSocket URL, but its audio capture pipeline actually produces raw 16-bit PCM. The server fails to decode. Separately, their chunk size (25ms) is below our documented 50ms minimum. Both are one-line fixes on their end. Verified live against production & documentation, not inferred from reading their code alone.

## Evidence

**1. Encoding mismatch (`Error 3006`)**

Their connection URL:
```
wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&encoding=opus&format_turns=true
```

Their audio capture (`AudioFormat`, and confirmed again in `writeWavHeader`, which writes a standard PCM WAV file locally) is unambiguously 16-bit signed little-endian PCM, not Opus. They're telling us one thing and sending another.

Reproduced against production with their exact URL and real synthesized PCM speech. Raw server response, exact:
```json
{
  "type": "Error",
  "error_code": 3006,
  "error": "User Input Validation Error: Failed to decode Opus packet: [Errno 1094995529] Invalid data found when processing input: 'avcodec_send_packet()'"
}
```
Connection closes on the first frame. Zero transcripts ever returned. This is a complete match for "doesn't work at all", as the client never got past frame one.

**2. Chunk size below minimum (`Error 3007`)**

`FRAMES_PER_BUFFER = 400` samples at 16kHz = 25ms per audio chunk. Our documented floor is 50ms ([common session errors and closures](https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures)).

Reproduced against production (encoding fixed, chunk size untouched). Raw server response, exact:
```json
{
  "type": "Error",
  "error_code": 3007,
  "error": "Input Duration Error: Input Duration Violation: 25.0 ms. Expected between 50 and 1000 ms"
}
```

This bug was invisible to the customer, Bug 1 kills the connection before any audio is sent, so they never got far enough to hit this one. If we'd only told them to fix the encoding, they'd have opened a second "still broken" ticket tomorrow.

**3. Confirms after both fixes**

Same URL, `encoding=pcm_s16le`, 50ms chunks, no `speech_model` set, sent real English and real Spanish audio separately:
```
"Your Honor, my client understands the charges."
"Su señoría, ¿mi cliente entiende los cargos?"
```
Both transcribe correctly. Default streaming model (`universal-3-5-pro`) handles their EN/ES use case natively, no additional config needed on their side beyond the two fixes above.

## Fix

Two one-line changes in their client:
- `encoding=opus` → `encoding=pcm_s16le`
- `FRAMES_PER_BUFFER = 400` → `800`

Full annotated diff in `FIXED_CODE.java` in this same folder, with comments explaining each change.

One more thing noted but **not fixed by us**: their `main()` instantiates `new StreamingTranscription()`, a class that doesn't exist in the file, the snippet as pasted into the ticket won't compile. Almost certainly a copy-paste artifact from when they pulled the snippet into the support thread, not their actual production code. Flagged in the fixed code and in the customer email for their confirmation; didn't assume anything further.

## Suggestions for the team (optional, low priority)

The `3006` error message is already specific and correctly named the actual problem (Opus decode failure). That part of the DX is fine. The one gap: nothing in their client surfaced that error to them in an actionable way before they filed "doesn't work at all", their `onError`/`onClose` handlers exist but just log to stderr, easy to miss in a noisy console. Not something we can fix on our end, but worth considering for a future SDK/quickstart template: a startup-time sanity check (or a more prominent doc callout) that flags "your declared `encoding` should match your actual audio format" given this looks like a plausible recurring footgun for anyone hand-rolling a WebSocket client instead of using an SDK.

**Scaling observation, worth a look during handoff:** the reference snippet spawns a dedicated `audioThread` per stream. Unclear whether that mirrors their actual production concurrency model or is just a CLI testing artifact, but worth checking. If they're running thousands of streams inside a single JVM instance, they risk native thread saturation and context-switching overhead well before 2,000 concurrent streams. Worth a quick architecture alignment to confirm they're on Virtual Threads or an async framework if their deployment is centralized rather than one process per stream.

## Docs bug found while researching (unrelated to this ticket)

The close code for "too many concurrent sessions" (new-sessions-per-minute limit exceeded) is documented as `1008` on [rate-limits](https://www.assemblyai.com/docs/streaming/rate-limits#what-happens-when-you-hit-the-limit), but as `3009` on [common session errors and closures](https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures#close-codes) - same message text, two different codes on two different pages. Not related to this ticket, but worth a docs fix since Spanglish (and presumably other customers scaling up) will be watching for this exact closure while ramping toward 2,000 streams.

## Bottom line

No action needed on our infrastructure. Customer's fix is in hand. Closing the loop with them directly.
