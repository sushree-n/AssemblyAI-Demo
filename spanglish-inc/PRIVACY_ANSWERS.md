# Data Privacy & Retention - Answers for Spanglish Inc.

Given your use case (court proceedings, often with sensitive PII), we want these answers to be precise and verifiable rather than reassuring-sounding. Every claim below links to the published AssemblyAI documentation or legal page it comes from, so your team can confirm independently.

## Direct answer

For AssemblyAI's Streaming product specifically (what you use), **Zero Data Retention is available today**: once your account is opted out of the model-training program, AssemblyAI retains **no audio and no transcripts** from your streaming sessions. Only certain transcript metadata (needed for logging and billing, e.g. session duration) is kept — not the audio or the transcribed text itself.

Source: [Data retention and model training — Streaming production environment](https://www.assemblyai.com/docs/data-retention-and-model-training#streaming-production-environment)

## Data lifecycle for a streaming session

- **In transit:** audio is sent over TLS 1.3 to AssemblyAI's streaming endpoint. ([Encryption](https://www.assemblyai.com/docs/data-retention-and-model-training#encryption))
- **At rest:** anything AssemblyAI does store is encrypted with AES-128 or AES-256. ([same source](https://www.assemblyai.com/docs/data-retention-and-model-training#encryption))
- **After the session ends, if you're opted out of model training (see below):** audio and transcripts are not retained. Only metadata for logging/billing purposes persists.
- **If you are *not* opted out of model training:** some files may be used to improve AssemblyAI's models, but only after an automated redaction pass designed to remove personally identifiable information first, and never if you're on a BAA or using AssemblyAI's EU servers. ([Model training](https://www.assemblyai.com/docs/data-retention-and-model-training#model-training)) We don't have a published fixed retention window specifically for streaming audio in this non-opted-out state, worth a direct question to AssemblyAI's privacy team if you want that number precisely, rather than us guessing. Given your use case, we'd recommend opting out (or signing a BAA, which opts you out automatically, see below) rather than relying on this path.

## How to get Zero Data Retention

Two ways to reach the ZDR state described above, both self-serve for paid accounts, both free:

1. **Toggle "Opt Out of Data Sharing for Model Improvement Program"** on the [Data Controls page](https://www.assemblyai.com/dashboard/settings/data-controls) in your dashboard. Requires Owner or Admin role. ([How to opt out](https://www.assemblyai.com/docs/faq/how-to-opt-out-of-data-sharing-for-our-model-improvement-program))
2. **Sign AssemblyAI's standard Business Associate Agreement (BAA).** Signing a BAA automatically opts you out of model training the moment it's signed, and that opt-out becomes permanent (the toggle can no longer be changed back). Also self-serve, from the same Data Controls page, at no additional cost. ([BAA FAQ](https://www.assemblyai.com/docs/faq/can-you-sign-a-baa), [how signing a BAA affects opt-out status](https://www.assemblyai.com/docs/data-controls#how-signing-a-baa-affects-your-opt-out-status), [standard BAA text](https://www.assemblyai.com/legal/business-associate-agreement))

Given you're processing court proceedings, we'd suggest the BAA route: it gets you ZDR and gives you an executed agreement to point to if this ever comes up in your own compliance reviews, rather than relying on a dashboard toggle alone.

## Compliance certifications

- **SOC 2 Type I and Type II** certified. Reports available through AssemblyAI's Trust Center. ([SOC2 certification](https://www.assemblyai.com/docs/data-retention-and-model-training#soc2-certification), [Trust Center](https://app.vanta.com/assemblyai/trust/7n80syl8zln1bn1qm3x8eg), [how to access reports](https://www.assemblyai.com/docs/faq/how-to-access-assemblyai-s-security-reports))
- **HIPAA:** AssemblyAI offers a BAA (same one referenced above) for processing Protected Health Information. Also cited as ISO 27001:2022 and PCI DSS v4.0 certified. ([Streaming HIPAA compliance](https://www.assemblyai.com/docs/streaming/medical-mode#hipaa-compliance))
- **GDPR:** built with GDPR principles in mind; see the [Privacy Policy](https://www.assemblyai.com/legal/privacy-policy) and [Data Processing Addendum](https://www.assemblyai.com/legal/data-processing-addendum) for the specifics. ([GDPR compliance](https://www.assemblyai.com/docs/data-retention-and-model-training#gdpr-compliance))
- **MFA:** enforced on internal systems that interface with customer data, and available for all customers on the dashboard. ([MFA FAQ](https://www.assemblyai.com/docs/faq/is-multi-factor-authentication-enforced-for-all-access-to-scoped-systems-and-data))
- **Vendor access:** documented Access Control Policy, with quarterly access and security reviews of vendors. ([Third-party review process](https://www.assemblyai.com/docs/faq/is-there-a-documented-process-for-reviewing-and-approving-third-party-service-providers))

We don't have a published breakdown of exactly which internal AssemblyAI roles can access customer data under normal operations beyond what's in the SOC 2 report itself, if your security team needs that level of detail, the SOC 2 report (available via the Trust Center link above) is the right source, or we can loop in AssemblyAI's security team directly.

## Data residency

Streaming has three endpoint options:

| Endpoint | URL | Behavior |
|---|---|---|
| Edge Routing (default) | `wss://streaming.assemblyai.com/v3/ws` | Lowest latency, auto-routes to nearest region |
| US data residency | `wss://streaming.us.assemblyai.com/v3/ws` | Audio and transcription data never leave the US |
| EU data residency | `wss://streaming.eu.assemblyai.com/v3/ws` | Audio and transcription data never leave the EU (AWS eu-north-1, Stockholm) |

Sources: [Streaming endpoints and data zones](https://www.assemblyai.com/docs/streaming/endpoints-and-data-zones), [EU servers FAQ](https://www.assemblyai.com/docs/faq/do-you-offer-servers-in-the-eu)

Not something you asked about, but if any of your proceedings involve EU-based parties, pinning to the EU endpoint is a one-line URL change and may be worth discussing.

## One more relevant safeguard: real-time PII redaction

Since your use case involves court proceedings, worth flagging that Streaming PII Redaction is available and can redact categories like names, phone numbers, email addresses, credit card numbers, Social Security numbers, and dates of birth directly from the live transcript, in addition to (not instead of) the retention posture above. ([Streaming PII redaction](https://www.assemblyai.com/docs/streaming/pii-redaction))

We tested this directly against `universal-3-5-pro` (the model your client already runs on) rather than assume compatibility from the docs alone, since this is exactly the kind of claim we didn't want to get wrong for you. Sent real speech containing a name, phone number, and email address:
- Without redaction: `"Hi, my name is Jack Thompson and you can reach me at 555-512-3456."` / `"Or jack@example.com."`
- With `redact_pii=true` on the same model: `"Hi, my name is [PERSON_NAME] [PERSON_NAME] and you can reach me at [PHONE_NUMBER]."` / `"Or [EMAIL_ADDRESS]."`

No raw PII reached the client in the redacted run, and the server explicitly echoed `redact_pii: true` back in its session-open response, confirming the parameter was applied, not silently ignored. Works cleanly with your model, no downgrade needed.

Two things worth knowing before you turn it on:
- **Final turns only.** Redaction applies to finalized transcripts, not partials. Enabling `redact_pii` automatically turns partial-turn delivery off by default so no unredacted text reaches the client, but if you ever explicitly re-enable partial turns (`include_partial_turns: true`) for UX reasons, those partials will contain unredacted PII alongside the redacted finals.
- **Text only, not audio.** Streaming PII redaction redacts the transcript text, not the underlying audio waveform. Redacted audio files are an async-only feature, not available on the streaming product.

## Summary

For your compliance team: opt out of model training or sign a BAA (both self-serve, no cost), and AssemblyAI retains no audio or transcript content from your streaming sessions, only minimal metadata for logging and billing. That's backed by SOC 2 Type I/II certification, a standard HIPAA BAA, and documented encryption in transit and at rest. Happy to get your security team directly in touch with AssemblyAI's privacy/security team if you want anything here confirmed firsthand or need the SOC 2 report itself.
