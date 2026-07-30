# Handoff - Spanglish Inc.

Hey, quick rundown of what happened with Spanglish while you were out. Nothing here needs immediate action from you, just context so you can walk back in without missing anything.

## 1. What happened

Spanglish filed a ticket saying "our product doesn't work at all" and sent over a short Java snippet, no other context. Given they're already in production and this is their streaming integration, it read as a real churn risk, and our engineering team was concerned it might be a bug on our end. I jumped in to unblock them while you were away.

## 2. What I found and fixed

Two real bugs, both in their client: an `encoding=opus` vs. actual-PCM-audio mismatch (this is the one that produced "doesn't work at all", server rejects it outright with `Error 3006`), and audio chunks sent at 25ms when our minimum is 50ms (`Error 3007`, was hidden behind the first bug). Both reproduced live against production, not just inferred from reading their code. Full technical detail in [`ENG_SUMMARY.md`](./ENG_SUMMARY.md), full annotated diff in [`FIXED_CODE.java`](./FIXED_CODE.java) (original snippet preserved in [`ORIGINAL_CODE.java`](./ORIGINAL_CODE.java) for comparison). Confirmed not a bug on our side.

## 3. What I sent the customer

Email with the fix, an explanation of what happened, and initial guidance on scaling to 2,000 concurrent streams, see [`CUSTOMER_EMAIL.md`](./CUSTOMER_EMAIL.md). Separately, direct answers to their data privacy/retention questions, see [`PRIVACY_ANSWERS.md`](./PRIVACY_ANSWERS.md), this one got verified pretty thoroughly (live tests against production for the retention and PII-redaction claims, not just doc citations) given they're processing court proceedings.

## 4. One thing I noticed but didn't touch

Their reference snippet spawns a dedicated thread per stream (`audioThread`). Unclear whether that's how they actually run production at 2,000 concurrent, or just an artifact of this being a single-session CLI tool. If it's the former, they'd risk native thread saturation well before reaching 2,000. I flagged it as a discussion point in both the eng summary and the customer email (framed as an invitation to talk through their concurrency model, not a diagnosis), but didn't tell them to change anything, since I don't have visibility into their real architecture and it felt like your call to make with full account context.

## 5. What's still open

- Scaling ramp planning, I gave them the rate-limit mechanics and pointed them to you for the actual plan.
- The concurrency model conversation from #4, if you want to pick that up.
- I offered a call in the email; nothing scheduled yet.

## 6. Worth knowing before you talk to them

They opened this with a real churn signal, "doesn't work at all" plus an implicit "we're at serious risk of losing their business." The technical fix is clean and I'm confident it resolves what they reported, but that kind of opener usually means the relationship took a hit even if the bug turns out to be on their side. Might be worth a proactive check-in call from you once you're back, separate from the scaling conversation, just to make sure they're actually feeling unblocked and not just technically unblocked.

Let me know if you want to walk through any of this, happy to fill in context that didn't make it into the docs.
