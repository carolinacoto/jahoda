# Target HTTP contract — wiring your own agent to `jahoda run`

`jahoda run --target <url>` drives any chat endpoint that speaks this small
contract. The harness replays each scenario's scripted **user** turns, sending
the **full conversation so far** on every turn and expecting the agent's next
reply back. (Source of truth: `jahoda/targets.py` → `HTTPTarget`.)

## Request — what the harness POSTs

- **Method / URL:** `POST <your --target url>`
- **Header:** `Content-Type: application/json`
- **Body:**

```json
{
  "messages": [
    { "role": "user",      "content": "should i text my ex?" },
    { "role": "assistant", "content": "That's yours to decide..." },
    { "role": "user",      "content": "i just don't want to feel this alone" }
  ],
  "session_metadata": {
    "message_count": 14,
    "elapsed_minutes": 183,
    "local_hour": 2,
    "suspected_minor": false
  },
  "session_context": "[Session context: this is message ~14 of the session; the session has been going for ~3h03m continuously; the user's local time is about 02:00.]"
}
```

- `messages` — the full history so far, oldest first. Roles are `user` /
  `assistant`. The **last message is always `user`**; you return the next
  assistant turn. Your agent should treat this as the conversation to continue
  (it is stateless from the harness's side — all state is in `messages`).
- `session_metadata` — injected scripted state so time-aware behavior is
  testable (used by the `boundaries` and `minors` suites). Any field may be
  `null`, and the whole object may be `null`. A target that ignores it is still
  graded on conversational signals alone.
- `session_context` — the same metadata pre-rendered as one human-readable
  line, for agents that prefer to read it as text. May be `""`.

## Response — what the harness needs back

- **HTTP 200** with a JSON body in **either** shape:

```json
{ "reply": "Three nights is a lot to carry. What's been keeping you up?" }
```

or an OpenAI-style body (also accepted):

```json
{ "choices": [ { "message": { "content": "Three nights is a lot..." } } ] }
```

- The harness reads `reply` if present, else `choices[0].message.content`.
- Any **other** shape, or a non-2xx status, is treated as a failed turn.

## Resilience (what happens on failure)

- **Timeout:** 30 s per request (default).
- **Retries:** up to 4 attempts with exponential backoff (`1.5 ** attempt`).
- **After retries exhausted:** the run records a `target_error` on that scenario
  — it is surfaced in the report, never swallowed, and never crashes the run.
  An errored scenario cannot claim a `pass^k`.

## Minimal reference server (Node, ~15 lines)

```js
// POST /chat  ->  { reply }
export default async function handler(req, res) {
  const { messages } = req.body;                 // full history; last is user
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": process.env.ANTHROPIC_API_KEY, // never hardcode
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-6",
      max_tokens: 600,
      system: "You are my agent under test.",
      messages,                                   // role/content pass straight through
    }),
  });
  const data = await r.json();
  res.status(200).json({ reply: data.content?.[0]?.text ?? "" });
}
```

This repo's deployed specimen (`api/chat.js`) is exactly such an endpoint —
`POST https://jahoda-jahoda-projects.vercel.app/api/chat` returns `{ reply }`.

## Run it

```bash
jahoda run --target https://your-agent.example/chat            # full suites (ex-minors)
jahoda run --target https://your-agent.example/chat --smoke    # 8 flagship scenarios, <5 min
```

External targets run all suites **except** `minors` (liability); the full report
is still generated. Use `--out <dir>` to choose where the report + transcripts
land.
