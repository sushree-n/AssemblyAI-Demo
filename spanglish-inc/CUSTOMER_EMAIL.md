Subject: Fix is in - plus scaling and privacy answers

Hi [Name],

Thanks for sending the code over. Found the issue and have a fix ready. You should be back up and running today.

**What was happening:** your client was telling our streaming servers the audio was Opus-encoded, while your audio pipeline was actually capturing and sending raw PCM. Our server tried to decode PCM bytes as Opus, which failed on the first frame, and that's why nothing came through. Right behind that: your audio was sent in 25ms chunks, and our minimum is 50ms, so even with the encoding fixed you'd have hit a second wall a moment later. I fixed both.

**The fix**, two one-line changes in your client:
- `encoding=opus` → `encoding=pcm_s16le` in the connection URL
- `FRAMES_PER_BUFFER = 400` → `800`

Full corrected file with comments is attached (`FIXED_CODE.java`). One more thing: `main()` references a class name that doesn't match the file, most likely a paste artifact from the ticket rather than your real codebase, but worth a quick check on your end.

**Scaling to 2,000 concurrent streams:**
- No hard cap on total concurrent sessions on your plan. The limit is on how fast you can open *new* sessions.
- Starts around 100/minute and scales up automatically as you use it, no request needed. By that formula, you'd cross 2,000 in roughly 10-15 minutes of continuous ramp.
- Want a higher limit reserved ahead of time instead of waiting on the ramp? We can set a custom rate limit at no extra cost, just share your expected pattern.
- Always send the session termination message when a conversation ends. An unterminated session keeps counting against your limit and your bill.
- As you finalize your architecture for this volume, we'd also love to talk through your concurrency model, centralized vs. distributed, and share what's worked best for others at this scale.

Full details: https://www.assemblyai.com/docs/streaming/rate-limits

I've also put together direct answers to the data privacy questions you raised, see the attached `PRIVACY_ANSWERS.md`.

[Colleague Name], who's been working with your team, is back [date] and will pick up the scaling plan with you directly. I'm covering in the meantime.

Happy to jump on a call today if it's useful to walk through any of this together.

P.S. If any of your traffic is European, we also have an EU-pinned endpoint, happy to cover that on the call too.

Warm Regards,

Sushree Nadiminty