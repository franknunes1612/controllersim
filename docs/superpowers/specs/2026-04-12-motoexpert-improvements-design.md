# MotoExpert AI — Improvements Design

**Date:** 2026-04-12
**Project:** `/Users/Bernardocoelho/Downloads/motoexpert/motoexpert/`
**Scope:** Bug fixes + UX polish + new features for public consumer deployment

---

## Context

MotoExpert AI is a Portuguese-language motorcycle assistant web app. Stack: single `index.html` frontend, Vercel Serverless Function backend (`api/chat.js`), Groq Llama 4 Scout as primary AI, Claude Haiku 4.5 as fallback. Targeting public sharing among motorcycle riders (B2C).

---

## 1. Architecture

Split the current monolithic `index.html` (1300+ lines) into three files:

```
public/
├── index.html      ← HTML structure only (~80 lines)
├── style.css       ← all CSS (unchanged styles)
└── app.js          ← all JS logic (refactored)

api/
└── chat.js         ← backend with streaming + bug fixes
```

`vercel.json` unchanged. No new npm dependencies. Deploys with `vercel --prod` as before.

---

## 2. Bug Fixes

| # | Bug | Fix |
|---|-----|-----|
| 1 | `data.error.message` — backend returns `{ error: 'string' }` but frontend accesses `.message` → always `undefined` | Change to `data.error` |
| 2 | Unused `sysPrompt()` function in frontend JS — dead code | Remove entirely |
| 3 | In-memory rate limiter resets on cold start — unreliable on Vercel serverless | Document as best-effort in code comments; proper fix (Redis) is out of scope |
| 4 | Chips truncate at 10 chars mid-word — "Yamaha MT-07" → "Yamaha MT-0" | Increase to 16 chars, truncate at word boundary |
| 5 | Budget bar formula (`budgetNum / 20`) fills at €2000 | Fix scale: €0–€5000 = 0–100% |
| 6 | "API LIVE" indicator always green, even after errors | Turn red on failed request, green on success |

---

## 3. UX Polish

1. **localStorage persistence** — bike context saved on every change, restored on load. Chat history persisted per session (capped at 50 messages), restored on refresh.

2. **Auto-close + switch** — saving the context panel closes it and switches to chat view automatically.

3. **Dynamic dashboard** — when no bike is configured, maintenance items show a "Configure a tua mota primeiro" placeholder. Once configured, items are relevant to context.

4. **Clear chat button** — small button in topbar; resets message history and shows welcome screen again.

5. **Onboarding nudge** — first time a message is sent without bike configured, a dismissible banner appears above the input: "Configura a tua mota para respostas mais precisas →". Shown once per session, stored in localStorage.

6. **Mobile input hint hidden** — "ENTER · ENVIAR" hint only rendered when `navigator.maxTouchPoints === 0` (non-touch devices).

---

## 4. New Features

### 4.1 Bike Autocomplete
- Typing in the bike field shows a dropdown of popular PT/EU models
- Dataset: Yamaha MT-07/09/10, Honda CB650R/CB1000R, Kawasaki Z650/Z900, BMW R1250GS/F900R, KTM Duke 390/890, Ducati Monster/Scrambler, Suzuki GSX-S750, Triumph Street Triple, Benelli TRK 502
- Filtered live by input value (case-insensitive)
- Free text entry still accepted for any model not in the list
- Implemented as a `<datalist>` element (zero JS complexity, native browser UX)

### 4.2 First-Visit Onboarding Modal
- Shown once on first visit (tracked via `localStorage` flag `moto_onboarded`)
- Modal contains the full context form inline (same fields as the side panel)
- CTA: "Vamos lá!" saves context and dismisses modal
- Secondary: "Saltar" dismisses without saving
- Not shown again after first interaction

### 4.3 Share Conversation
- Each AI response bubble gets a share icon button (📋) in the top-right corner
- On click: copies a clean plain-text summary to clipboard
  ```
  🏍️ MotoExpert AI
  Mota: [bike] ([year])
  Pergunta: [user message]
  
  [resposta_principal]
  
  Recomendações:
  • [rec 1]
  • [rec 2]
  
  Via motoexpert.vercel.app
  ```
- Toast notification: "Copiado! ✓" appears for 2 seconds
- Share button only visible on hover (desktop) or always visible (mobile)

### 4.4 Streaming Responses
- Backend: `stream: true` added to Groq API call; response piped as `text/event-stream`
- Frontend: uses `ReadableStream` on the `fetch` response
- As chunks arrive: raw text appended to a temporary plain bubble (replaces typing indicator)
- When stream ends: full accumulated text parsed as JSON and temp bubble replaced with structured card
- If JSON parse fails: raw text remains as plain response (existing fallback preserved)
- Haiku fallback: does NOT stream (Anthropic streaming requires different handling); falls back to existing non-streaming flow
- Error states:
  - Stream interrupted mid-response → partial raw text shown with "⚠ Resposta incompleta" label
  - Rate limit (429) → existing message + countdown timer (60s)

---

## 5. Data Flow

```
localStorage → ctx object → sent with every POST /api/chat
                                      ↓
                              buildSystemPrompt(ctx)
                                      ↓
                         Groq Llama 4 Scout (stream: true)
                                      ↓ chunks
                         ReadableStream → temp bubble
                                      ↓ stream end
                         JSON.parse → structured card
                                      ↓ (if parse fails)
                         raw text plain bubble
```

**Conversation history:** Stored in `localStorage` as `moto_history`. Capped at last 50 messages. Trimmed automatically when cap is reached. Sent to backend capped at existing `MAX_HISTORY = 6` turns.

---

## 6. Out of Scope

- Redis-based rate limiting (requires external service)
- Multilingual support
- User accounts / cloud history sync
- Bike database API (using static datalist instead)
- Anthropic streaming fallback
- PWA / offline mode
