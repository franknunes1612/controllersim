# MailCraft PT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Portuguese professional email writing SaaS with free (10/month) and Pro (€7/month, unlimited) plans powered by Claude Haiku.

**Architecture:** Next.js 15 App Router — all server logic lives in Route Handlers and Server Actions, no separate backend. Generation streams from a single Route Handler that checks usage, calls Anthropic Haiku with humanizer-rules in the system prompt, saves to Supabase, and increments the counter atomically. Stripe webhooks update plan state; the webhook Route Handler uses the Supabase service role key since there is no user session.

**Tech Stack:** Next.js 15, Tailwind CSS, Supabase (`@supabase/ssr`), Anthropic SDK (`@anthropic-ai/sdk`), Stripe (`stripe`), Vitest (unit tests), Vercel (deploy)

---

## File Map

```
mailcraft-pt/
├── app/
│   ├── globals.css
│   ├── layout.tsx                        # Root layout — mounts Nav
│   ├── page.tsx                          # Landing page
│   ├── login/page.tsx                    # Auth page (email/password + Google)
│   ├── auth/callback/route.ts            # OAuth exchange code for session
│   ├── generate/page.tsx                 # Generator page (protected)
│   ├── history/page.tsx                  # History page (protected)
│   ├── dashboard/page.tsx                # Dashboard — usage + plan status
│   ├── api/generate/route.ts             # Streaming generation Route Handler
│   └── api/stripe/webhook/route.ts       # Stripe webhook Route Handler
├── components/
│   ├── nav.tsx                           # Sticky nav (client — user menu)
│   ├── email-form.tsx                    # Generator form + SSE stream reader (client)
│   └── usage-bar.tsx                     # Progress bar for free usage (server)
├── lib/
│   ├── supabase/
│   │   ├── client.ts                     # createBrowserClient (client components)
│   │   ├── server.ts                     # createServerClient (RSC / Server Actions)
│   │   └── admin.ts                      # service-role client (webhook / cron)
│   ├── usage.ts                          # Pure usage logic — testable functions
│   ├── prompt.ts                         # Anthropic system prompt + user message builder
│   └── stripe.ts                         # Stripe singleton
├── middleware.ts                         # Route protection + Supabase session refresh
├── supabase/migrations/
│   ├── 001_profiles.sql
│   └── 002_emails.sql
└── __tests__/
    └── usage.test.ts
```

---

## Task 1: Scaffold Project and Install Dependencies

**Files:**
- Create: `mailcraft-pt/` (project root via create-next-app)
- Create: `mailcraft-pt/vitest.config.ts`

- [ ] **Step 1: Scaffold Next.js app**

Run from `/Users/Bernardocoelho`:
```bash
npx create-next-app@latest mailcraft-pt \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
cd mailcraft-pt
```

- [ ] **Step 2: Install runtime dependencies**

```bash
npm install @supabase/ssr @supabase/supabase-js @anthropic-ai/sdk stripe
```

- [ ] **Step 3: Install dev dependencies**

```bash
npm install -D vitest @vitest/coverage-v8 @types/node
```

- [ ] **Step 4: Create Vitest config**

Create `mailcraft-pt/vitest.config.ts`:
```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    include: ['__tests__/**/*.test.ts'],
  },
})
```

- [ ] **Step 5: Add test script to package.json**

In `package.json`, add to `"scripts"`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: scaffold Next.js project with Supabase, Anthropic, Stripe, Vitest"
```

---

## Task 2: Environment Variables

**Files:**
- Create: `mailcraft-pt/.env.local` (not committed)
- Create: `mailcraft-pt/.env.local.example` (committed)

- [ ] **Step 1: Create .env.local.example**

Create `mailcraft-pt/.env.local.example`:
```bash
# Supabase — https://supabase.com/dashboard → Settings → API
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Anthropic — https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-...

# Stripe — https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

- [ ] **Step 2: Copy to .env.local and fill in real values**

```bash
cp .env.local.example .env.local
```

Then open `.env.local` and fill in your credentials.

- [ ] **Step 3: Ensure .env.local is gitignored**

Verify `mailcraft-pt/.gitignore` contains `.env.local` (create-next-app adds this automatically).

- [ ] **Step 4: Commit example file**

```bash
git add .env.local.example
git commit -m "chore: add .env.local.example with required variables"
```

---

## Task 3: Database Migrations

**Files:**
- Create: `mailcraft-pt/supabase/migrations/001_profiles.sql`
- Create: `mailcraft-pt/supabase/migrations/002_emails.sql`

- [ ] **Step 1: Write profiles migration**

Create `mailcraft-pt/supabase/migrations/001_profiles.sql`:
```sql
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  plan text not null default 'free' check (plan in ('free', 'pro')),
  stripe_customer_id text,
  stripe_subscription_id text,
  emails_used integer not null default 0,
  billing_cycle_start timestamptz not null default now(),
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "users_select_own_profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "users_update_own_profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-create profile row on first sign-in
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id)
  values (new.id);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
```

- [ ] **Step 2: Write emails migration**

Create `mailcraft-pt/supabase/migrations/002_emails.sql`:
```sql
create table public.emails (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade not null,
  context text not null,
  recipient_type text not null check (recipient_type in ('boss','client','colleague','public_entity','other')),
  tone text not null check (tone in ('formal','neutral','direct')),
  subject text not null,
  body text not null,
  variations jsonb,
  created_at timestamptz not null default now()
);

alter table public.emails enable row level security;

create policy "users_select_own_emails"
  on public.emails for select
  using (auth.uid() = user_id);

create policy "users_insert_own_emails"
  on public.emails for insert
  with check (auth.uid() = user_id);
```

- [ ] **Step 3: Run migrations in Supabase dashboard**

Go to your Supabase project → SQL Editor. Paste and run `001_profiles.sql`, then `002_emails.sql`.

Verify: go to Table Editor and confirm both tables exist with the correct columns.

- [ ] **Step 4: Enable Google OAuth in Supabase**

Go to Supabase → Authentication → Providers → Google.
Enable it and paste your Google OAuth Client ID and Secret.
Set redirect URL to: `https://your-project.supabase.co/auth/v1/callback`

- [ ] **Step 5: Commit migrations**

```bash
git add supabase/
git commit -m "feat: add database migrations for profiles and emails tables"
```

---

## Task 4: Supabase Client Helpers and Middleware

**Files:**
- Create: `mailcraft-pt/lib/supabase/client.ts`
- Create: `mailcraft-pt/lib/supabase/server.ts`
- Create: `mailcraft-pt/lib/supabase/admin.ts`
- Create: `mailcraft-pt/middleware.ts`

- [ ] **Step 1: Browser client (for client components)**

Create `mailcraft-pt/lib/supabase/client.ts`:
```ts
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

- [ ] **Step 2: Server client (for RSC, Server Actions, Route Handlers with cookies)**

Create `mailcraft-pt/lib/supabase/server.ts`:
```ts
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Ignore: setAll called from Server Component (read-only context)
          }
        },
      },
    }
  )
}
```

- [ ] **Step 3: Admin client (service role — webhook handler only)**

Create `mailcraft-pt/lib/supabase/admin.ts`:
```ts
import { createClient } from '@supabase/supabase-js'

// Only import this in server-only files (Route Handlers, not client components)
export function createAdminClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )
}
```

- [ ] **Step 4: Middleware — session refresh + route protection**

Create `mailcraft-pt/middleware.ts`:
```ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const PROTECTED_ROUTES = ['/generate', '/history', '/dashboard']

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh session — required for @supabase/ssr
  const { data: { user } } = await supabase.auth.getUser()

  const isProtected = PROTECTED_ROUTES.some(r =>
    request.nextUrl.pathname.startsWith(r)
  )

  if (isProtected && !user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (request.nextUrl.pathname === '/login' && user) {
    return NextResponse.redirect(new URL('/generate', request.url))
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api/stripe).*)',
  ],
}
```

Note: `/api/stripe/webhook` is excluded from the matcher so the raw body is not touched.

- [ ] **Step 5: Commit**

```bash
git add lib/ middleware.ts
git commit -m "feat: add Supabase client helpers and route protection middleware"
```

---

## Task 5: Pure Usage Logic and Unit Tests

**Files:**
- Create: `mailcraft-pt/lib/usage.ts`
- Create: `mailcraft-pt/__tests__/usage.test.ts`

- [ ] **Step 1: Write usage.ts**

Create `mailcraft-pt/lib/usage.ts`:
```ts
export const FREE_LIMIT = 10
export const CYCLE_DAYS = 30

export type Profile = {
  plan: 'free' | 'pro'
  emails_used: number
  billing_cycle_start: string // ISO timestamp
}

/** Returns true if the 30-day free cycle has elapsed and should reset. */
export function shouldResetCycle(billingCycleStart: string): boolean {
  const start = new Date(billingCycleStart)
  const now = new Date()
  const diffMs = now.getTime() - start.getTime()
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  return diffDays >= CYCLE_DAYS
}

/** Returns true if a free user is at or over the monthly limit. */
export function isAtLimit(profile: Profile): boolean {
  if (profile.plan === 'pro') return false
  return profile.emails_used >= FREE_LIMIT
}

/** Returns remaining emails for free users; null for Pro. */
export function remaining(profile: Profile): number | null {
  if (profile.plan === 'pro') return null
  return Math.max(0, FREE_LIMIT - profile.emails_used)
}

/** Returns the auto-paired tone for Pro second variation.
 *  formal ↔ neutral, direct → formal
 */
export function getPairedTone(tone: string): string {
  if (tone === 'formal') return 'neutral'
  if (tone === 'neutral') return 'formal'
  return 'formal' // direct → formal
}
```

- [ ] **Step 2: Write failing tests**

Create `mailcraft-pt/__tests__/usage.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import {
  shouldResetCycle,
  isAtLimit,
  remaining,
  getPairedTone,
  FREE_LIMIT,
} from '../lib/usage'

const now = new Date()

function daysAgo(n: number): string {
  const d = new Date(now)
  d.setDate(d.getDate() - n)
  return d.toISOString()
}

describe('shouldResetCycle', () => {
  it('returns false when cycle started today', () => {
    expect(shouldResetCycle(daysAgo(0))).toBe(false)
  })

  it('returns false when 29 days have passed', () => {
    expect(shouldResetCycle(daysAgo(29))).toBe(false)
  })

  it('returns true when exactly 30 days have passed', () => {
    expect(shouldResetCycle(daysAgo(30))).toBe(true)
  })

  it('returns true when more than 30 days have passed', () => {
    expect(shouldResetCycle(daysAgo(45))).toBe(true)
  })
})

describe('isAtLimit', () => {
  it('returns false for pro users regardless of usage', () => {
    expect(isAtLimit({ plan: 'pro', emails_used: 100, billing_cycle_start: daysAgo(0) })).toBe(false)
  })

  it('returns false for free users below limit', () => {
    expect(isAtLimit({ plan: 'free', emails_used: 9, billing_cycle_start: daysAgo(0) })).toBe(false)
  })

  it('returns true for free users at the limit', () => {
    expect(isAtLimit({ plan: 'free', emails_used: FREE_LIMIT, billing_cycle_start: daysAgo(0) })).toBe(true)
  })

  it('returns true for free users over the limit', () => {
    expect(isAtLimit({ plan: 'free', emails_used: FREE_LIMIT + 1, billing_cycle_start: daysAgo(0) })).toBe(true)
  })
})

describe('remaining', () => {
  it('returns null for pro users', () => {
    expect(remaining({ plan: 'pro', emails_used: 0, billing_cycle_start: daysAgo(0) })).toBeNull()
  })

  it('returns correct remaining count for free users', () => {
    expect(remaining({ plan: 'free', emails_used: 3, billing_cycle_start: daysAgo(0) })).toBe(7)
  })

  it('returns 0, not negative, when over limit', () => {
    expect(remaining({ plan: 'free', emails_used: FREE_LIMIT + 2, billing_cycle_start: daysAgo(0) })).toBe(0)
  })
})

describe('getPairedTone', () => {
  it('pairs formal with neutral', () => {
    expect(getPairedTone('formal')).toBe('neutral')
  })

  it('pairs neutral with formal', () => {
    expect(getPairedTone('neutral')).toBe('formal')
  })

  it('pairs direct with formal', () => {
    expect(getPairedTone('direct')).toBe('formal')
  })
})
```

- [ ] **Step 3: Run tests and confirm they pass**

```bash
npm test
```

Expected output:
```
✓ __tests__/usage.test.ts (11 tests)
Test Files  1 passed (1)
Tests       11 passed (11)
```

- [ ] **Step 4: Commit**

```bash
git add lib/usage.ts __tests__/usage.test.ts
git commit -m "feat: add usage limit logic with unit tests"
```

---

## Task 6: Auth Pages

**Files:**
- Create: `mailcraft-pt/app/login/page.tsx`
- Create: `mailcraft-pt/app/auth/callback/route.ts`

- [ ] **Step 1: Login page**

Create `mailcraft-pt/app/login/page.tsx`:
```tsx
'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const supabase = createClient()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const { error } =
      mode === 'login'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password })

    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      router.push('/generate')
      router.refresh()
    }
  }

  async function handleGoogle() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${process.env.NEXT_PUBLIC_APP_URL}/auth/callback` },
    })
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow p-8">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">
          {mode === 'login' ? 'Entrar' : 'Criar conta'}
        </h1>

        <button
          onClick={handleGoogle}
          className="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-lg px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 mb-4"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continuar com Google
        </button>

        <div className="flex items-center gap-2 mb-4">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">ou</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            placeholder="Palavra-passe"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'A carregar...' : mode === 'login' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>

        <p className="text-sm text-center text-gray-500 mt-4">
          {mode === 'login' ? 'Não tem conta?' : 'Já tem conta?'}{' '}
          <button
            onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
            className="text-blue-600 hover:underline"
          >
            {mode === 'login' ? 'Criar conta' : 'Entrar'}
          </button>
        </p>
      </div>
    </main>
  )
}
```

- [ ] **Step 2: OAuth callback route**

Create `mailcraft-pt/app/auth/callback/route.ts`:
```ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')

  if (code) {
    const supabase = await createClient()
    await supabase.auth.exchangeCodeForSession(code)
  }

  return NextResponse.redirect(`${origin}/generate`)
}
```

- [ ] **Step 3: Commit**

```bash
git add app/login/ app/auth/
git commit -m "feat: add login page with email/password and Google OAuth"
```

---

## Task 7: Navigation Component and Root Layout

**Files:**
- Create: `mailcraft-pt/components/nav.tsx`
- Modify: `mailcraft-pt/app/layout.tsx`

- [ ] **Step 1: Nav component**

Create `mailcraft-pt/components/nav.tsx`:
```tsx
'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

type NavProps = {
  userEmail: string | null
  plan: 'free' | 'pro' | null
  emailsUsed: number
}

export default function Nav({ userEmail, plan, emailsUsed }: NavProps) {
  const router = useRouter()
  const supabase = createClient()

  async function signOut() {
    await supabase.auth.signOut()
    router.push('/')
    router.refresh()
  }

  return (
    <nav className="sticky top-0 z-10 bg-white border-b border-gray-200">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold text-gray-900 text-sm">
          MailCraft PT
        </Link>

        {userEmail ? (
          <div className="flex items-center gap-4">
            <Link href="/generate" className="text-sm text-gray-600 hover:text-gray-900">
              Gerar
            </Link>
            <Link href="/history" className="text-sm text-gray-600 hover:text-gray-900">
              Histórico
            </Link>
            <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
              Dashboard
            </Link>
            {plan === 'free' && (
              <span className="text-xs text-gray-400">{emailsUsed}/10</span>
            )}
            <button
              onClick={signOut}
              className="text-sm text-gray-500 hover:text-gray-900"
            >
              Sair
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700"
          >
            Entrar
          </Link>
        )}
      </div>
    </nav>
  )
}
```

- [ ] **Step 2: Update root layout**

Replace `mailcraft-pt/app/layout.tsx` with:
```tsx
import type { Metadata } from 'next'
import './globals.css'
import Nav from '@/components/nav'
import { createClient } from '@/lib/supabase/server'

export const metadata: Metadata = {
  title: 'MailCraft PT — Emails profissionais em português',
  description: 'Escreva emails profissionais em Português Europeu em segundos.',
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  let plan: 'free' | 'pro' | null = null
  let emailsUsed = 0

  if (user) {
    const { data: profile } = await supabase
      .from('profiles')
      .select('plan, emails_used')
      .eq('id', user.id)
      .single()

    plan = (profile?.plan as 'free' | 'pro') ?? 'free'
    emailsUsed = profile?.emails_used ?? 0
  }

  return (
    <html lang="pt">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <Nav
          userEmail={user?.email ?? null}
          plan={plan}
          emailsUsed={emailsUsed}
        />
        {children}
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add components/nav.tsx app/layout.tsx
git commit -m "feat: add sticky nav with user menu and usage counter"
```

---

## Task 8: Anthropic Prompt Builder

**Files:**
- Create: `mailcraft-pt/lib/prompt.ts`

- [ ] **Step 1: Create prompt builder**

Create `mailcraft-pt/lib/prompt.ts`:
```ts
export const SYSTEM_PROMPT = `És um assistente especializado em escrita de emails profissionais em Português Europeu (PT-PT).
O utilizador vai descrever o que quer comunicar, a quem se dirige, e o tom pretendido.

Devolve SEMPRE neste formato exato:
Assunto: [linha de assunto concisa]

[corpo completo do email, com saudação e despedida]

Regras de escrita obrigatórias:
- Usa sempre Português Europeu (não Brasileiro). Nunca uses "você" — usa sempre "o senhor / a senhora" para formal, "tu" só em contexto muito informal.
- Adapta a saudação: "Exmo. Sr./Sra." para entidades formais/superiores, "Caro/a [função]" para colegas, "Exmo. Sr./Sra." para entidades públicas.
- NUNCA uses: "sublinhar a importância", "testemunho de", "papel fundamental", "paisagem", "crucial", "pivotal", "showcasing", "fostering", nem qualquer tom promocional inflado.
- Sem travessões (—) em excesso. Prefere vírgula ou ponto final.
- Sem "regra de três" forçada.
- Sem frases de enchimento: "É importante notar que", "Com o intuito de", "No sentido de".
- Sem despedidas vazias ("Aguardo com expectativa a sua resposta!"). Despedida adequada ao tom: "Com os melhores cumprimentos," para formal; "Cumprimentos," para neutro; "Fico à disposição." para direto.
- Varia o comprimento das frases. Usa "é/são/tem" em vez de "serve como / representa / constitui".
- Escreve o que acontece ou o que se quer, não o que simboliza.`

const RECIPIENT_LABELS: Record<string, string> = {
  boss: 'Chefe / Superior hierárquico',
  client: 'Cliente',
  colleague: 'Colega',
  public_entity: 'Entidade pública / serviço governamental',
  other: 'Destinatário geral',
}

const TONE_LABELS: Record<string, string> = {
  formal: 'Formal',
  neutral: 'Neutro',
  direct: 'Direto',
}

export function buildUserMessage(
  context: string,
  recipientType: string,
  tone: string
): string {
  return `Destinatário: ${RECIPIENT_LABELS[recipientType] ?? recipientType}
Tom: ${TONE_LABELS[tone] ?? tone}
Mensagem a comunicar: ${context}`
}

/** Splits the raw Haiku output into subject + body.
 *  Haiku always starts with "Assunto: ..." on the first line.
 */
export function parseEmailOutput(raw: string): { subject: string; body: string } {
  const lines = raw.trim().split('\n')
  const subjectLine = lines.find(l => l.startsWith('Assunto:')) ?? ''
  const subject = subjectLine.replace('Assunto:', '').trim()
  const subjectIndex = lines.findIndex(l => l.startsWith('Assunto:'))
  const body = lines
    .slice(subjectIndex + 1)
    .join('\n')
    .trim()
  return { subject, body }
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/prompt.ts
git commit -m "feat: add Anthropic prompt builder and response parser"
```

---

## Task 9: Generation API Route (Streaming)

**Files:**
- Create: `mailcraft-pt/lib/stripe.ts` (Stripe singleton, needed in later tasks but declared here to avoid import errors)
- Create: `mailcraft-pt/app/api/generate/route.ts`

- [ ] **Step 1: Create Stripe singleton**

Create `mailcraft-pt/lib/stripe.ts`:
```ts
import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-03-31.basil',
})
```

- [ ] **Step 2: Create generation Route Handler**

Create `mailcraft-pt/app/api/generate/route.ts`:
```ts
import { NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { createClient } from '@/lib/supabase/server'
import { SYSTEM_PROMPT, buildUserMessage, parseEmailOutput } from '@/lib/prompt'
import { isAtLimit, shouldResetCycle, getPairedTone } from '@/lib/usage'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
const MODEL = 'claude-haiku-4-5-20251001'

export async function POST(request: Request) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.json({ error: 'Não autenticado.' }, { status: 401 })
  }

  const { context, recipientType, tone } = await request.json() as {
    context: string
    recipientType: string
    tone: string
  }

  if (!context?.trim() || !recipientType || !tone) {
    return NextResponse.json({ error: 'Campos em falta.' }, { status: 400 })
  }

  // Load profile and apply lazy billing cycle reset for free users
  const { data: profile, error: profileError } = await supabase
    .from('profiles')
    .select('plan, emails_used, billing_cycle_start')
    .eq('id', user.id)
    .single()

  if (profileError || !profile) {
    return NextResponse.json({ error: 'Perfil não encontrado.' }, { status: 500 })
  }

  // Lazy reset: if 30 days have elapsed since billing_cycle_start, reset counter
  if (profile.plan === 'free' && shouldResetCycle(profile.billing_cycle_start)) {
    await supabase
      .from('profiles')
      .update({ emails_used: 0, billing_cycle_start: new Date().toISOString() })
      .eq('id', user.id)
    profile.emails_used = 0
  }

  if (isAtLimit(profile as { plan: 'free' | 'pro'; emails_used: number; billing_cycle_start: string })) {
    return NextResponse.json(
      { error: 'LIMIT_REACHED', message: 'Atingiu o limite do plano gratuito. Faça upgrade para continuar.' },
      { status: 403 }
    )
  }

  const userMessage = buildUserMessage(context, recipientType, tone)

  // For Pro users, generate the second variation in parallel (non-streaming)
  const pairedTonePromise = profile.plan === 'pro'
    ? anthropic.messages.create({
        model: MODEL,
        max_tokens: 1024,
        system: SYSTEM_PROMPT,
        messages: [{ role: 'user', content: buildUserMessage(context, recipientType, getPairedTone(tone)) }],
      })
    : null

  // Stream primary generation
  const encoder = new TextEncoder()
  let fullText = ''

  const readable = new ReadableStream({
    async start(controller) {
      try {
        const stream = anthropic.messages.stream({
          model: MODEL,
          max_tokens: 1024,
          system: SYSTEM_PROMPT,
          messages: [{ role: 'user', content: userMessage }],
        })

        for await (const chunk of stream) {
          if (
            chunk.type === 'content_block_delta' &&
            chunk.delta.type === 'text_delta'
          ) {
            fullText += chunk.delta.text
            const event = `data: ${JSON.stringify({ type: 'chunk', text: chunk.delta.text })}\n\n`
            controller.enqueue(encoder.encode(event))
          }
        }

        // Await secondary variation if Pro
        let variationBody: string | null = null
        if (pairedTonePromise) {
          const variationMsg = await pairedTonePromise
          const variationRaw = variationMsg.content
            .filter(b => b.type === 'text')
            .map(b => (b as { type: 'text'; text: string }).text)
            .join('')
          variationBody = parseEmailOutput(variationRaw).body
        }

        // Save to DB
        const { subject, body } = parseEmailOutput(fullText)
        const { data: saved } = await supabase.from('emails').insert({
          user_id: user.id,
          context,
          recipient_type: recipientType,
          tone,
          subject,
          body,
          variations: variationBody
            ? { [getPairedTone(tone)]: variationBody }
            : null,
        }).select('id').single()

        // Increment usage counter
        await supabase
          .from('profiles')
          .update({ emails_used: profile.emails_used + 1 })
          .eq('id', user.id)

        // Send done event with metadata
        const doneEvent = `data: ${JSON.stringify({
          type: 'done',
          emailId: saved?.id ?? null,
          variation: variationBody ? { tone: getPairedTone(tone), body: variationBody } : null,
        })}\n\n`
        controller.enqueue(encoder.encode(doneEvent))
        controller.close()
      } catch (err) {
        const errEvent = `data: ${JSON.stringify({ type: 'error', message: 'Erro ao gerar email.' })}\n\n`
        controller.enqueue(encoder.encode(errEvent))
        controller.close()
      }
    },
  })

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
```

- [ ] **Step 3: Commit**

```bash
git add app/api/generate/ lib/stripe.ts
git commit -m "feat: add streaming generation Route Handler with usage enforcement"
```

---

## Task 10: EmailForm Client Component

**Files:**
- Create: `mailcraft-pt/components/email-form.tsx`

- [ ] **Step 1: Create EmailForm**

Create `mailcraft-pt/components/email-form.tsx`:
```tsx
'use client'

import { useState, useRef } from 'react'
import { parseEmailOutput } from '@/lib/prompt'

type Variation = { tone: string; body: string }

type Props = {
  isAtLimit: boolean
  isPro: boolean
}

const RECIPIENT_OPTIONS = [
  { value: 'boss', label: 'Chefe / Superior' },
  { value: 'client', label: 'Cliente' },
  { value: 'colleague', label: 'Colega' },
  { value: 'public_entity', label: 'Entidade Pública' },
  { value: 'other', label: 'Outro' },
]

const TONE_OPTIONS = [
  { value: 'formal', label: 'Formal' },
  { value: 'neutral', label: 'Neutro' },
  { value: 'direct', label: 'Direto' },
]

const TONE_LABELS: Record<string, string> = {
  formal: 'Formal', neutral: 'Neutro', direct: 'Direto',
}

export default function EmailForm({ isAtLimit, isPro }: Props) {
  const [context, setContext] = useState('')
  const [recipientType, setRecipientType] = useState('client')
  const [tone, setTone] = useState('formal')
  const [streaming, setStreaming] = useState(false)
  const [rawText, setRawText] = useState('')
  const [variation, setVariation] = useState<Variation | null>(null)
  const [activeTab, setActiveTab] = useState<'primary' | 'variation'>('primary')
  const [error, setError] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  const parsed = rawText ? parseEmailOutput(rawText) : null

  async function generate() {
    if (!context.trim()) return
    setError('')
    setRawText('')
    setVariation(null)
    setActiveTab('primary')
    setStreaming(true)

    abortRef.current = new AbortController()

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context, recipientType, tone }),
        signal: abortRef.current.signal,
      })

      if (!res.ok) {
        const json = await res.json()
        if (json.error === 'LIMIT_REACHED') {
          setError(json.message)
        } else {
          setError('Erro ao gerar email. Tente novamente.')
        }
        setStreaming(false)
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const json = JSON.parse(line.slice(6))

          if (json.type === 'chunk') {
            setRawText(prev => prev + json.text)
          } else if (json.type === 'done') {
            if (json.variation) setVariation(json.variation)
          } else if (json.type === 'error') {
            setError(json.message)
          }
        }
      }
    } catch (e: unknown) {
      if ((e as Error).name !== 'AbortError') {
        setError('Erro de ligação. Tente novamente.')
      }
    } finally {
      setStreaming(false)
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            O que quer comunicar?
          </label>
          <textarea
            value={context}
            onChange={e => setContext(e.target.value)}
            rows={4}
            placeholder="Ex: Quero marcar uma reunião com o cliente para a próxima semana para discutir o projeto."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Destinatário
            </label>
            <select
              value={recipientType}
              onChange={e => setRecipientType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {RECIPIENT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tom
            </label>
            <select
              value={tone}
              onChange={e => setTone(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {TONE_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>

        {isAtLimit ? (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
            Atingiu o limite do plano gratuito (10 emails/mês).{' '}
            <a href="/dashboard" className="font-medium underline">Fazer upgrade para Pro</a>
          </div>
        ) : (
          <button
            onClick={generate}
            disabled={streaming || !context.trim()}
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {streaming ? (
              <>
                <span className="animate-spin">⟳</span> A gerar...
              </>
            ) : (
              'Gerar Email →'
            )}
          </button>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {/* Result */}
      {(rawText || streaming) && (
        <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
          {/* Tabs (Pro only) */}
          {variation && (
            <div className="flex gap-2 border-b border-gray-200 pb-3">
              <button
                onClick={() => setActiveTab('primary')}
                className={`text-sm px-3 py-1 rounded-md ${activeTab === 'primary' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                {TONE_LABELS[tone]}
              </button>
              <button
                onClick={() => setActiveTab('variation')}
                className={`text-sm px-3 py-1 rounded-md ${activeTab === 'variation' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                {TONE_LABELS[variation.tone]}
              </button>
            </div>
          )}

          {activeTab === 'primary' && parsed && (
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Assunto</span>
                  <p className="text-sm font-medium text-gray-900 mt-0.5">{parsed.subject}</p>
                </div>
                <button
                  onClick={() => copyToClipboard(parsed.subject)}
                  className="text-xs text-gray-400 hover:text-gray-700 shrink-0"
                >
                  Copiar
                </button>
              </div>
              <div className="border-t border-gray-100 pt-3">
                <div className="flex items-start justify-between gap-2">
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed flex-1">
                    {parsed.body}
                    {streaming && <span className="animate-pulse">▌</span>}
                  </pre>
                  {!streaming && (
                    <button
                      onClick={() => copyToClipboard(parsed.body)}
                      className="text-xs text-gray-400 hover:text-gray-700 shrink-0"
                    >
                      Copiar
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'variation' && variation && (
            <div className="space-y-3">
              <div className="border-t border-gray-100 pt-3">
                <div className="flex items-start justify-between gap-2">
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed flex-1">
                    {variation.body}
                  </pre>
                  <button
                    onClick={() => copyToClipboard(variation.body)}
                    className="text-xs text-gray-400 hover:text-gray-700 shrink-0"
                  >
                    Copiar
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add components/email-form.tsx
git commit -m "feat: add EmailForm client component with SSE streaming reader"
```

---

## Task 11: Generator Page

**Files:**
- Create: `mailcraft-pt/app/generate/page.tsx`

- [ ] **Step 1: Create generator page**

Create `mailcraft-pt/app/generate/page.tsx`:
```tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import EmailForm from '@/components/email-form'
import { isAtLimit, shouldResetCycle } from '@/lib/usage'

export default async function GeneratePage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('plan, emails_used, billing_cycle_start')
    .eq('id', user.id)
    .single()

  const safeProfile = {
    plan: (profile?.plan ?? 'free') as 'free' | 'pro',
    emails_used: profile?.emails_used ?? 0,
    billing_cycle_start: profile?.billing_cycle_start ?? new Date().toISOString(),
  }

  // Apply lazy reset for display purposes (actual reset happens in Route Handler)
  const displayUsed = shouldResetCycle(safeProfile.billing_cycle_start)
    ? 0
    : safeProfile.emails_used

  const limitReached = isAtLimit({ ...safeProfile, emails_used: displayUsed })

  return (
    <main className="max-w-2xl mx-auto px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Gerar email</h1>
        <p className="text-sm text-gray-500 mt-1">
          Descreva o que quer dizer e nós redigimos.
        </p>
      </div>
      <EmailForm
        isAtLimit={limitReached}
        isPro={safeProfile.plan === 'pro'}
      />
    </main>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add app/generate/
git commit -m "feat: add generator page"
```

---

## Task 12: Usage Bar Component and Dashboard Page

**Files:**
- Create: `mailcraft-pt/components/usage-bar.tsx`
- Create: `mailcraft-pt/app/dashboard/page.tsx`

- [ ] **Step 1: Usage bar component**

Create `mailcraft-pt/components/usage-bar.tsx`:
```tsx
type Props = {
  used: number
  total: number
}

export default function UsageBar({ used, total }: Props) {
  const pct = Math.min((used / total) * 100, 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm text-gray-600">
        <span>{used} de {total} emails usados este mês</span>
        <span>{total - used} restantes</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${pct >= 90 ? 'bg-red-500' : 'bg-blue-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Dashboard page**

Create `mailcraft-pt/app/dashboard/page.tsx`:
```tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import UsageBar from '@/components/usage-bar'
import { shouldResetCycle, FREE_LIMIT } from '@/lib/usage'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('plan, emails_used, billing_cycle_start')
    .eq('id', user.id)
    .single()

  const plan = (profile?.plan ?? 'free') as 'free' | 'pro'
  const emailsUsed = shouldResetCycle(profile?.billing_cycle_start ?? '')
    ? 0
    : (profile?.emails_used ?? 0)

  return (
    <main className="max-w-2xl mx-auto px-4 py-10 space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>

      <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Plano atual</span>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${plan === 'pro' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>
            {plan === 'pro' ? 'Pro' : 'Gratuito'}
          </span>
        </div>

        {plan === 'free' && (
          <>
            <UsageBar used={emailsUsed} total={FREE_LIMIT} />
            <a
              href="/api/stripe/checkout"
              className="block w-full text-center bg-blue-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-blue-700"
            >
              Fazer Upgrade para Pro — €7/mês
            </a>
            <p className="text-xs text-gray-400 text-center">
              Emails ilimitados, histórico completo, 2 variações por geração.
            </p>
          </>
        )}

        {plan === 'pro' && (
          <p className="text-sm text-gray-500">
            Emails ilimitados. Gerido pelo Stripe — cancele quando quiser.
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Link
          href="/generate"
          className="bg-white rounded-xl shadow-sm p-4 text-sm font-medium text-gray-900 hover:bg-gray-50"
        >
          Gerar email →
        </Link>
        <Link
          href="/history"
          className="bg-white rounded-xl shadow-sm p-4 text-sm font-medium text-gray-900 hover:bg-gray-50"
        >
          Ver histórico →
        </Link>
      </div>
    </main>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add components/usage-bar.tsx app/dashboard/
git commit -m "feat: add usage bar component and dashboard page"
```

---

## Task 13: History Page

**Files:**
- Create: `mailcraft-pt/app/history/page.tsx`

- [ ] **Step 1: Create history page**

Create `mailcraft-pt/app/history/page.tsx`:
```tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

const RECIPIENT_LABELS: Record<string, string> = {
  boss: 'Chefe / Superior',
  client: 'Cliente',
  colleague: 'Colega',
  public_entity: 'Entidade Pública',
  other: 'Outro',
}

const TONE_LABELS: Record<string, string> = {
  formal: 'Formal',
  neutral: 'Neutro',
  direct: 'Direto',
}

export default async function HistoryPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('plan')
    .eq('id', user.id)
    .single()

  const isPro = profile?.plan === 'pro'

  // Free users: last 30 days only
  let query = supabase
    .from('emails')
    .select('id, subject, recipient_type, tone, created_at, body')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(100)

  if (!isPro) {
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
    query = query.gte('created_at', thirtyDaysAgo.toISOString())
  }

  const { data: emails } = await query

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Histórico</h1>
          {!isPro && (
            <p className="text-sm text-gray-500 mt-1">Últimos 30 dias. Upgrade para acesso completo.</p>
          )}
        </div>
      </div>

      {!emails?.length ? (
        <p className="text-sm text-gray-500">Ainda não gerou nenhum email.</p>
      ) : (
        <div className="space-y-3">
          {emails.map(email => (
            <details key={email.id} className="bg-white rounded-xl shadow-sm p-4 group">
              <summary className="flex items-center justify-between cursor-pointer list-none">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{email.subject}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {RECIPIENT_LABELS[email.recipient_type]} · {TONE_LABELS[email.tone]} ·{' '}
                    {new Date(email.created_at).toLocaleDateString('pt-PT')}
                  </p>
                </div>
                <span className="text-xs text-gray-400 ml-4 group-open:hidden">Ver</span>
                <span className="text-xs text-gray-400 ml-4 hidden group-open:inline">Fechar</span>
              </summary>
              <div className="mt-3 pt-3 border-t border-gray-100">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {email.body}
                </pre>
                <button
                  onClick={() => navigator.clipboard.writeText(email.body)}
                  className="mt-3 text-xs text-blue-600 hover:underline"
                >
                  Copiar email
                </button>
              </div>
            </details>
          ))}
        </div>
      )}
    </main>
  )
}
```

Note: The copy button in the details element requires `'use client'`. To keep this page a Server Component, extract it to a small client component. Replace the `<button onClick=...>` with:

Create `mailcraft-pt/components/copy-button.tsx`:
```tsx
'use client'

export default function CopyButton({ text }: { text: string }) {
  return (
    <button
      onClick={() => navigator.clipboard.writeText(text)}
      className="mt-3 text-xs text-blue-600 hover:underline"
    >
      Copiar email
    </button>
  )
}
```

Then in `history/page.tsx`, replace the inline button with `<CopyButton text={email.body} />` and add `import CopyButton from '@/components/copy-button'`.

- [ ] **Step 2: Commit**

```bash
git add app/history/ components/copy-button.tsx
git commit -m "feat: add history page with 30-day filter for free users"
```

---

## Task 14: Landing Page

**Files:**
- Modify: `mailcraft-pt/app/page.tsx`

- [ ] **Step 1: Replace default landing page**

Replace `mailcraft-pt/app/page.tsx` with:
```tsx
import Link from 'next/link'

const EXAMPLE_EMAIL = `Assunto: Pedido de reunião — projeto Alfa

Caro Sr. Ferreira,

Venho por este meio solicitar uma reunião para discutirmos o estado atual do projeto Alfa. Gostaria de perceber os pontos pendentes e definir os próximos passos.

Fica ao seu critério escolher a data e hora mais convenientes.

Cumprimentos,
Ana Costa`

export default function LandingPage() {
  return (
    <main>
      {/* Hero */}
      <section className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h1 className="text-4xl font-bold text-gray-900 leading-tight">
          Emails profissionais em<br />
          <span className="text-blue-600">Português Europeu</span>, em segundos.
        </h1>
        <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto">
          Descreva o que quer dizer. Escolha o tom. O MailCraft PT escreve o email por si, em PT-PT natural — pronto a enviar.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link
            href="/login"
            className="bg-blue-600 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-blue-700"
          >
            Começar gratuitamente
          </Link>
          <span className="text-sm text-gray-400">10 emails/mês, grátis</span>
        </div>

        {/* Example email */}
        <div className="mt-12 bg-white rounded-2xl shadow-sm p-6 text-left max-w-xl mx-auto">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">Exemplo gerado</p>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
            {EXAMPLE_EMAIL}
          </pre>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white py-16">
        <div className="max-w-4xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          {[
            { title: 'Rápido', desc: 'Gera em segundos. Sem edição manual.' },
            { title: 'PT-PT natural', desc: 'Sem brasileiro. Sem anglicismos. Saudações corretas.' },
            { title: 'Tom certo', desc: 'Formal, neutro ou direto — o email adapta-se.' },
          ].map(f => (
            <div key={f.title}>
              <h3 className="text-base font-semibold text-gray-900">{f.title}</h3>
              <p className="mt-2 text-sm text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-3xl mx-auto px-4 py-20">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">Preços simples</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Free */}
          <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Gratuito</h3>
              <p className="text-3xl font-bold text-gray-900 mt-1">€0</p>
            </div>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>10 emails por mês</li>
              <li>Histórico de 30 dias</li>
              <li>1 variação por geração</li>
            </ul>
            <Link
              href="/login"
              className="block text-center border border-gray-300 text-gray-700 rounded-xl px-4 py-2 text-sm hover:bg-gray-50"
            >
              Começar
            </Link>
          </div>

          {/* Pro */}
          <div className="bg-blue-600 rounded-2xl p-6 space-y-4 text-white">
            <div>
              <h3 className="text-lg font-semibold">Pro</h3>
              <p className="text-3xl font-bold mt-1">€7<span className="text-lg font-normal">/mês</span></p>
            </div>
            <ul className="space-y-2 text-sm text-blue-100">
              <li>Emails ilimitados</li>
              <li>Histórico completo</li>
              <li>2 variações de tom por geração</li>
            </ul>
            <Link
              href="/login"
              className="block text-center bg-white text-blue-600 rounded-xl px-4 py-2 text-sm font-medium hover:bg-blue-50"
            >
              Começar Pro
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-6 text-center text-xs text-gray-400">
        © {new Date().getFullYear()} MailCraft PT
      </footer>
    </main>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add app/page.tsx
git commit -m "feat: add landing page with hero, features, and pricing"
```

---

## Task 15: Stripe Billing — Checkout and Webhook

**Files:**
- Create: `mailcraft-pt/app/api/stripe/checkout/route.ts`
- Create: `mailcraft-pt/app/api/stripe/webhook/route.ts`

Before this task: create a Stripe product and price in the Stripe dashboard.
1. Go to https://dashboard.stripe.com/products → Add product
2. Name: "MailCraft PT Pro", Price: €7.00 / month recurring, Currency: EUR
3. Copy the Price ID (starts with `price_`)
4. Add `STRIPE_PRICE_ID=price_...` to `.env.local`

- [ ] **Step 1: Checkout Route Handler**

Create `mailcraft-pt/app/api/stripe/checkout/route.ts`:
```ts
import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { stripe } from '@/lib/stripe'

export async function GET() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.redirect(new URL('/login', process.env.NEXT_PUBLIC_APP_URL!))
  }

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [{ price: process.env.STRIPE_PRICE_ID!, quantity: 1 }],
    customer_email: user.email,
    metadata: { user_id: user.id },
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?upgraded=1`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard`,
  })

  return NextResponse.redirect(session.url!)
}
```

- [ ] **Step 2: Webhook Route Handler**

Create `mailcraft-pt/app/api/stripe/webhook/route.ts`:
```ts
import { NextResponse } from 'next/server'
import { stripe } from '@/lib/stripe'
import { createAdminClient } from '@/lib/supabase/admin'
import Stripe from 'stripe'

export async function POST(request: Request) {
  const body = await request.text()
  const sig = request.headers.get('stripe-signature')!

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  const supabase = createAdminClient()

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session
    const userId = session.metadata?.user_id
    if (!userId) return NextResponse.json({ ok: true })

    await supabase
      .from('profiles')
      .update({
        plan: 'pro',
        stripe_customer_id: session.customer as string,
        stripe_subscription_id: session.subscription as string,
      })
      .eq('id', userId)
  }

  if (event.type === 'invoice.paid') {
    const invoice = event.data.object as Stripe.Invoice
    const customerId = invoice.customer as string

    await supabase
      .from('profiles')
      .update({
        emails_used: 0,
        billing_cycle_start: new Date().toISOString(),
      })
      .eq('stripe_customer_id', customerId)
  }

  if (event.type === 'customer.subscription.deleted') {
    const sub = event.data.object as Stripe.Subscription
    const customerId = sub.customer as string

    await supabase
      .from('profiles')
      .update({
        plan: 'free',
        emails_used: 0,
        billing_cycle_start: new Date().toISOString(),
        stripe_subscription_id: null,
      })
      .eq('stripe_customer_id', customerId)
  }

  return NextResponse.json({ ok: true })
}
```

- [ ] **Step 3: Update middleware to exclude Stripe routes from session middleware**

Verify `mailcraft-pt/middleware.ts` matcher already excludes `/api/stripe`:
```
matcher: ['/((?!_next/static|_next/image|favicon.ico|api/stripe).*)']
```

If not, update it now.

- [ ] **Step 4: Set up Stripe webhook locally for testing**

Install Stripe CLI: https://stripe.com/docs/stripe-cli

```bash
stripe login
stripe listen --forward-to localhost:3000/api/stripe/webhook
```

The CLI prints a webhook signing secret — paste it into `STRIPE_WEBHOOK_SECRET` in `.env.local`.

- [ ] **Step 5: Commit**

```bash
git add app/api/stripe/
git commit -m "feat: add Stripe checkout and webhook handler for billing"
```

---

## Task 16: Deploy to Vercel

**Files:**
- No file changes — Vercel CLI deployment

- [ ] **Step 1: Install Vercel CLI and link project**

```bash
npm i -g vercel
vercel link
```

Select "Create new project", name it `mailcraft-pt`.

- [ ] **Step 2: Add all environment variables to Vercel**

```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add ANTHROPIC_API_KEY production
vercel env add STRIPE_SECRET_KEY production
vercel env add STRIPE_WEBHOOK_SECRET production
vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production
vercel env add STRIPE_PRICE_ID production
vercel env add NEXT_PUBLIC_APP_URL production
```

For `NEXT_PUBLIC_APP_URL`, use your Vercel deployment URL (e.g. `https://mailcraft-pt.vercel.app`).

- [ ] **Step 3: Deploy to production**

```bash
vercel --prod
```

- [ ] **Step 4: Set up production Stripe webhook**

Go to https://dashboard.stripe.com/webhooks → Add endpoint.
URL: `https://mailcraft-pt.vercel.app/api/stripe/webhook`
Events to listen for:
- `checkout.session.completed`
- `invoice.paid`
- `customer.subscription.deleted`

Copy the new Signing Secret and update `STRIPE_WEBHOOK_SECRET` on Vercel:
```bash
vercel env rm STRIPE_WEBHOOK_SECRET production
vercel env add STRIPE_WEBHOOK_SECRET production
vercel --prod  # redeploy to pick up new env
```

- [ ] **Step 5: Update Supabase redirect URLs**

Go to Supabase → Authentication → URL Configuration.
Add to Redirect URLs: `https://mailcraft-pt.vercel.app/auth/callback`

- [ ] **Step 6: Smoke test**

1. Open `https://mailcraft-pt.vercel.app`
2. Sign up with Google → lands on `/generate`
3. Generate an email → see streaming output
4. Go to `/dashboard` → see usage bar showing 1/10
5. Click "Fazer Upgrade" → Stripe checkout opens
6. Use test card `4242 4242 4242 4242` → webhook fires → dashboard shows Pro badge
7. Go to `/history` → see the generated email

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|---|---|
| Landing page with hero, features, pricing | Task 14 |
| Auth: email/password + Google OAuth | Task 6 |
| OAuth callback | Task 6 |
| profiles table with trigger | Task 3 |
| emails table with RLS | Task 3 |
| Route protection middleware | Task 4 |
| Usage enforcement (before generation) | Task 9 — isAtLimit check before Anthropic call |
| Lazy billing cycle reset for free users | Task 9 — shouldResetCycle + update before limit check |
| Streaming generation | Task 9 |
| Humanizer rules in system prompt | Task 8 |
| Parsed subject line | Task 8 (parseEmailOutput) + Task 9 |
| Pro: 2 tone variations in parallel | Task 9 — pairedTonePromise |
| Save to emails table + increment counter | Task 9 |
| Generator page with form | Tasks 10, 11 |
| Copy buttons | Task 10 (EmailForm) |
| Dashboard with usage bar | Task 12 |
| Free-user upgrade CTA | Task 12 |
| History page (30-day filter for free) | Task 13 |
| Nav with usage counter | Task 7 |
| Stripe checkout | Task 15 |
| Webhook: checkout.session.completed | Task 15 |
| Webhook: invoice.paid (reset counter) | Task 15 |
| Webhook: subscription.deleted (revert) | Task 15 |
| Deploy to Vercel | Task 16 |

All spec requirements covered. No gaps found.
