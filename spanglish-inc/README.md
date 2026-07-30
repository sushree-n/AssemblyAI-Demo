# Spanglish Inc. — Critical Issue

Part 2 of the take-home ([repo root](../README.md)). A production customer (Spanglish Inc., English/Spanish note-taking for court proceedings) reported their AssemblyAI streaming integration "doesn't work at all." Their assigned Applied AI Engineer was out of office; this covers the diagnosis, fix, and the resulting communications while covering their account.

## Suggested reading order

1. **[`ENG_SUMMARY.md`](./ENG_SUMMARY.md)** — start here for the technical grounding. TL;DR: not a bug on AssemblyAI's side, two client-side misconfigurations, both reproduced live against the production streaming endpoint (not just inferred from reading the code).
2. **[`CUSTOMER_EMAIL.md`](./CUSTOMER_EMAIL.md)** — the main deliverable. Covers the fix, scaling guidance for 2,000 concurrent streams, and hands off to the privacy doc.
3. **[`PRIVACY_ANSWERS.md`](./PRIVACY_ANSWERS.md)** — data retention/privacy answers for their compliance side. Every claim is either sourced to a specific AssemblyAI doc page or, where the stakes were high enough (data retention, PII redaction on their exact model), verified with a live test rather than a doc citation.
4. **[`FIXED_CODE.java`](./FIXED_CODE.java)** — the minimal corrected client, with comments only where something changed. [`ORIGINAL_CODE.java`](./ORIGINAL_CODE.java) is the customer's snippet as sent, for side-by-side diffing.
5. **[`HANDOFF.md`](./HANDOFF.md)** — for the Applied AI Engineer who actually owns this account, back from OOO. What happened, what got sent, one observation deliberately not acted on, and what's still open.

## The two bugs

1. **`encoding=opus` declared in the connection URL while the client actually captures and sends raw PCM audio.** Server rejects the mismatch (`Error 3006`) on the first frame — this is the "doesn't work at all" symptom.
2. **25ms audio chunks, below AssemblyAI's documented 50ms minimum** (`Error 3007`). Hidden behind bug #1 until that one's fixed.

Both are one-line fixes on the customer's side. Full detail in `ENG_SUMMARY.md`.
