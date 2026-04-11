# MailCraft PT — Design Spec

**Date:** 2026-04-11
**Status:** Approved

---

## Overview

MailCraft PT is a SaaS product that helps Portuguese users (PT-PT) write professional emails. Users describe what they want to say, specify who they are writing to and the desired tone, and the app generates a complete, natural-sounding professional email in European Portuguese — ready to copy.

**Target users:** Portuguese professionals, freelancers, small business owners, and anyone who needs to write formal or semi-formal emails regularly in PT-PT.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 15 (App Router) |
| Auth + Database | Supabase (Postgres + Auth) |
| AI | Anthropic Claude Haiku |
| Billing | Stripe |
| Deployment | Vercel |

---

## Plans

| Feature | Free | Pro (€7/month) |
|---|---|---|
| Emails per month | 10 | Unlimited |
| Email history | Last 30 days | Full |
| Tone variations per generation | 1 | 2 (side by side) |
| Generated subject line | Yes | Yes |

Usage resets on the user's billing cycle date (not calendar month) to avoid pro-rata confusion. Free users reset monthly from their sign-up date.

---

## Routes

```
/                    Landing page
/login               Auth (email/password + Google OAuth)
/auth/callback       OAuth redirect handler
/generate            Main email generator (protected)
/history             Saved email history (protected)
/dashboard           Usage stats + plan status (protected)
/api/stripe/webhook  Stripe webhook Route Handler
```

---

## Data Model

### `profiles` table
Extends `auth.users`. Created automatically via Supabase database trigger on first sign-in.

| Column | Type | Notes |
|---|---|---|
| id | UUID | FK → auth.users |
| plan | text | `'free'` or `'pro'` |
| stripe_customer_id | text | nullable |
| stripe_subscription_id | text | nullable |
| emails_used | int | default 0 |
| billing_cycle_start | timestamp | set on sign-up, reset on renewal |
| created_at | timestamp | |

### `emails` table

| Column | Type | Notes |
|---|---|---|
| id | UUID | |
| user_id | UUID | FK → profiles |
| context | text | What the user typed |
| recipient_type | text | boss, client, colleague, public_entity, other |
| tone | text | formal, neutral, direct |
| subject | text | Generated subject line |
| body | text | Generated email body |
| variations | jsonb | `{ formal: "...", neutral: "..." }` — Pro only |
| created_at | timestamp | |

Stripe is the source of truth for subscription state. We only cache `stripe_subscription_id` and `plan` locally.

---

## Key Flows

### Auth
- Supabase Auth handles login/signup (email/password + Google OAuth)
- On first sign-in, a Postgres trigger creates a `profiles` row with `plan = 'free'` and `emails_used = 0`
- OAuth callback at `/auth/callback` completes the session and redirects to `/generate`

### Email Generation
1. User fills form: context (textarea), recipient type (dropdown), tone (dropdown)
2. Submit triggers a Server Action
3. Server Action queries `profiles`:
   - For free users: if `now() > billing_cycle_start + 30 days`, reset `emails_used = 0` and update `billing_cycle_start = now()` (lazy reset — no cron required)
   - If `plan = 'free'` and `emails_used >= 10`, return error with upgrade prompt
4. Call Anthropic Haiku with a PT-PT system prompt that incorporates recipient type and tone
   - For Pro users: make two parallel Haiku calls — one for the chosen tone, one for the auto-paired variation (formal ↔ neutral; direct is always paired with formal)
5. Stream primary response back to the UI (user sees email being written in real-time)
6. On stream complete: insert row into `emails` table (including `variations` jsonb for Pro), increment `emails_used` on `profiles`
7. UI displays: suggested subject line + email body + copy buttons
8. Pro users see both tone variations in tabs labelled with the tone name

### Upgrade Flow
1. User hits limit or clicks "Fazer Upgrade" → Server Action creates a Stripe Checkout Session (€7/month, recurring)
2. User is redirected to Stripe hosted checkout
3. On payment success: Stripe sends `checkout.session.completed` webhook → update `plan = 'pro'`, store `stripe_customer_id` and `stripe_subscription_id`
4. User is redirected to `/dashboard` with Pro badge confirmed

### Cancellation
- Stripe sends `customer.subscription.deleted` webhook → revert `plan = 'free'`, set `billing_cycle_start = now()` to start a fresh 30-day free window
- User's email history is preserved (but access reverts to last-30-days view)
- `emails_used` resets to 0 on cancellation (fresh start on free plan)

---

## UI Structure

### Landing Page (`/`)
- Hero: PT-PT headline, subheadline, CTA to sign up, static example of a generated email
- Feature row: "Rápido", "Português Europeu natural", "Tom profissional"
- Pricing table: Free vs Pro side by side
- Footer: links, copyright

### Generator (`/generate`)
```
┌─────────────────────────────────────────────────────┐
│ O que quer comunicar?                               │
│ [textarea — main input]                             │
│                                                     │
│ [Destinatário ▼]          [Tom ▼]                  │
│                                                     │
│ [Gerar Email →]                                     │
└─────────────────────────────────────────────────────┘

── resultado ─────────────────────────────────────────
Assunto: Solicitação de reunião          [copiar]
─────────────────────────────────────────────────────
Exmo. Sr. Silva,

Venho por este meio...                   [copiar]
─────────────────────────────────────────────────────
[variation 2 — Pro only, shown in second tab/column]
```

**Recipient type options:** Chefe / Superior, Cliente, Colega, Entidade Pública, Outro
**Tone options:** Formal, Neutro, Direto

### Dashboard (`/dashboard`)
- Plan badge: "Plano Gratuito" or "Plano Pro"
- Usage bar (free only): "7 de 10 emails usados este mês" with progress bar
- "Fazer Upgrade" CTA (free users only)
- Quick links: Gerar email, Ver histórico

### History (`/history`)
- Table: date, recipient type, tone, subject preview
- Click row to expand: full body + copy button
- Free users see last 30 days; Pro users see full history

### Navigation (shared)
- Sticky top nav: logo, "Gerar", "Histórico", "Dashboard", user avatar menu (sign out)

---

## AI Prompt Design

**System prompt (PT-PT):**
```
És um assistente especializado em escrita de emails profissionais em Português Europeu (PT-PT).
O utilizador vai descrever o que quer comunicar, a quem se dirige, e o tom pretendido.
Devolve SEMPRE:
1. Uma linha de assunto concisa (prefixada com "Assunto:")
2. O corpo completo do email, com saudação e despedida adequadas ao destinatário e tom.
Usa sempre Português Europeu (não Brasileiro). Não uses anglicismos desnecessários.
Adapta a saudação ao destinatário: "Exmo. Sr./Sra." para entidades formais, "Caro/a [nome/função]" para colegas, etc.
```

**User message format:**
```
Destinatário: {recipient_type}
Tom: {tone}
Mensagem a comunicar: {context}
```

---

## Usage Enforcement

- Check happens **before** calling Anthropic (fail fast, no wasted tokens)
- Counter increments **after** successful generation (not on error)
- Free limit: 10 emails/month
- Upgrade prompt shown inline in the generator when limit is reached
- Usage counter shown in the nav for free users (e.g. "3/10")

---

## Stripe Integration

- **Product:** MailCraft PT Pro
- **Price:** €7/month recurring
- **Webhook events handled:**
  - `checkout.session.completed` → activate Pro
  - `invoice.paid` → reset `emails_used = 0`, update `billing_cycle_start`
  - `customer.subscription.deleted` → revert to Free

---

## What's Out of Scope (MVP)

- Email templates / saved prompts
- Team/organisation accounts
- Custom domain email sending
- Annual pricing
- Mobile app
- Multilingual support (PT only for now)
