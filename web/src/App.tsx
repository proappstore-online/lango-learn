import { useState } from 'react'
import { ActionError, initPro, ProShell, PageHeader, useAuth, type NavItem } from '@proappstore/sdk'
import { newGuestProgress, readGuestProgress, saveGuestProgress, type GuestProgress } from './guest-progress'

const app = initPro({ appId: 'lango-learn' })
const NAV: NavItem[] = [
  { label: 'Home', href: '/', title: 'Lango Learn' },
  { label: 'About', href: '/about', title: 'About — Lango Learn' },
]

export default function App() {
  const { user, loading, signIn } = useAuth(app)
  if (loading) return <main className="mx-auto max-w-3xl px-6 py-16" aria-live="polite">Checking your account…</main>
  if (!user) return window.location.pathname === '/about' ? <GuestAbout signIn={signIn} /> : <GuestHome signIn={signIn} />
  return <ProShell app={app} appName="Lango Learn" nav={NAV} branding="app">
    {window.location.pathname === '/about' ? <About /> : <Home userId={user.id} name={user.name ?? 'learner'} />}
  </ProShell>
}

function GuestFrame({ children, signIn }: { children: React.ReactNode; signIn: () => void }) {
  return <main className="mx-auto w-full max-w-3xl px-6 py-10 sm:py-16">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <a href="/" className="font-semibold text-[var(--accent-deep)]">Lango Learn</a>
      <button type="button" onClick={signIn} className="rounded-xl bg-[var(--accent-deep)] px-5 py-2 font-semibold text-white">Sign in with GitHub</button>
    </div>
    {children}
  </main>
}

const PROMPTS = [
  { phrase: 'Hola', question: 'What does “Hola” mean?', choices: ['Hello', 'Thank you'], answer: 'Hello' },
  { phrase: 'Gracias', question: 'What does “Gracias” mean?', choices: ['Goodbye', 'Thank you'], answer: 'Thank you' },
]

function GuestHome({ signIn }: { signIn: () => void }) {
  const [progress, setProgress] = useState<GuestProgress | null>(() => {
    const saved = readGuestProgress()
    return saved?.claimedBy ? null : saved
  })
  const [storageOk, setStorageOk] = useState(true)
  const [feedback, setFeedback] = useState('')
  const step = progress?.completedSteps ?? 0

  function begin() {
    const next = newGuestProgress()
    setStorageOk(saveGuestProgress(next))
    setProgress(next)
    setFeedback('')
  }

  function answer(choice: string) {
    if (!progress || step >= PROMPTS.length) return
    if (choice !== PROMPTS[step].answer) {
      setFeedback('Try again. You can read the phrase above before choosing.')
      return
    }
    const next = { ...progress, completedSteps: step + 1, savedAt: Date.now() }
    setStorageOk(saveGuestProgress(next))
    setProgress(next)
    setFeedback('That’s right.')
  }

  return <GuestFrame signIn={signIn}>
    <PageHeader title="Lango Learn" description="Try a short sample without an account." />
    <section className="mt-8 rounded-2xl border border-[var(--line-strong)] bg-[var(--panel-strong)] p-6 shadow-[var(--shadow-card)] sm:p-8" aria-labelledby="sample-title">
      <p className="text-sm font-semibold uppercase tracking-widest text-[var(--accent-deep)]">Local sample · Spanish greetings</p>
      <h2 id="sample-title" className="display-font mt-3 text-3xl font-semibold">A first look at two useful words</h2>
      <p className="mt-4 leading-7 text-[var(--muted)]">This is a small preview, not a published course lesson or graded achievement. Your place is kept only in this browser until you sign in and choose to import it.</p>
      {!progress ? <button type="button" onClick={begin} className="mt-6 rounded-xl bg-[var(--accent-deep)] px-5 py-2 font-semibold text-white">Start local sample</button> : step < PROMPTS.length ? <div className="mt-6">
        <p className="text-sm text-[var(--muted)]">Step {step + 1} of {PROMPTS.length}</p>
        <p className="mt-2 text-2xl font-semibold" lang="es">{PROMPTS[step].phrase}</p>
        <h3 className="mt-3 text-lg font-semibold">{PROMPTS[step].question}</h3>
        <div className="mt-4 flex flex-wrap gap-3">{PROMPTS[step].choices.map(choice => <button key={choice} type="button" onClick={() => answer(choice)} className="rounded-xl border border-[var(--line-strong)] px-5 py-2 font-semibold hover:bg-[var(--accent-soft)]">{choice}</button>)}</div>
        <p className="mt-3" role="status">{feedback}</p>
      </div> : <div className="mt-6"><p className="font-semibold" role="status">Sample complete in this browser.</p><p className="mt-2 text-[var(--muted)]">Sign in to save this sample checkpoint to your account. Course progress will begin when a reviewed course is available.</p></div>}
      {progress && <button type="button" onClick={begin} className="mt-6 block text-sm underline">Start this sample again</button>}
      {!storageOk && <p role="alert" className="mt-4 text-[var(--danger)]">Browser storage is unavailable. This place will be lost when you leave this page.</p>}
    </section>
    <p className="mt-6 text-sm text-[var(--muted)]">No lesson data is sent to the server before sign-in. <a href="/about" className="inline-flex items-center underline">About the course</a></p>
  </GuestFrame>
}

type Receipt = { id: string; completed_steps: number; outcome: 'imported' | 'kept_existing' }
function rows(value: unknown): Record<string, unknown>[] {
  if (!value || typeof value !== 'object' || !('rows' in value)) throw new Error('Unexpected response from the lesson service.')
  const found = (value as { rows: unknown }).rows
  if (!Array.isArray(found)) throw new Error('Unexpected response from the lesson service.')
  return found as Record<string, unknown>[]
}

function ImportPanel({ userId }: { userId: string }) {
  const [progress, setProgress] = useState(() => readGuestProgress())
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  if (!progress) return null
  if (progress.claimedBy && progress.claimedBy !== userId) return <p className="mt-6" role="status">A local sample on this browser was already imported to another account. It cannot be moved to this account.</p>

  async function importProgress() {
    if (!progress || busy) return
    setBusy(true)
    setMessage('')
    try {
      await app.actions.call('import_guest_lesson', { guest_session_id: progress.id, completed_steps: progress.completedSteps, client_saved_at: progress.savedAt })
      const receiptRows = rows(await app.actions.call('get_guest_import_receipt', { guest_session_id: progress.id }))
      const receipt = receiptRows[0] as Receipt | undefined
      if (!receipt) {
        setMessage('This sample ID is already claimed by another account or could not be imported. Your local copy is still here.')
      } else if (receipt.completed_steps !== progress.completedSteps) {
        setMessage(`A previous import saved ${receipt.completed_steps} of 2 steps. This browser has ${progress.completedSteps} of 2. Your local copy is still here; start a new sample to save a new checkpoint.`)
      } else {
        const next = { ...progress, claimedBy: userId }
        if (saveGuestProgress(next)) setProgress(next)
        setMessage(receipt.outcome === 'kept_existing' ? 'Your account already had an equal or later sample checkpoint. Both records are kept; your best checkpoint stays available.' : `Saved ${receipt.completed_steps} of 2 sample steps to your account. This is unverified sample history, not graded course progress.`)
      }
    } catch (error) {
      if (error instanceof ActionError && error.status === 429) setMessage('Too many requests. Try again later; your local copy is safe.')
      else if (error instanceof ActionError && error.status >= 400 && error.status < 500) setMessage('The import was rejected. Your local copy is safe; refresh and try again.')
      else setMessage('The import could not be confirmed. Your local copy is safe; retrying with the same ID will check the original result.')
    } finally { setBusy(false) }
  }

  return <section className="mt-8 rounded-2xl border border-[var(--line-strong)] bg-[var(--panel-strong)] p-6" aria-labelledby="import-title">
    <h2 id="import-title" className="text-xl font-semibold">Local sample found</h2>
    <p className="mt-2 text-[var(--muted)]">This browser has {progress.completedSteps} of 2 sample steps. Importing keeps an unverified copy on your account and never replaces course progress.</p>
    {!progress.claimedBy && <button type="button" aria-label="Save sample to my account" disabled={busy} onClick={importProgress} className="mt-4 rounded-xl bg-[var(--accent-deep)] px-5 py-2 font-semibold text-white disabled:opacity-50">{busy ? 'Checking import…' : 'Save sample to my account'}</button>}
    {progress.claimedBy === userId && !message && <p className="mt-4">This sample was saved to this account.</p>}
    {message && <p className="mt-4" role="status">{message}</p>}
  </section>
}

function Home({ userId, name }: { userId: string; name: string }) {
  return <div className="mx-auto w-full max-w-3xl px-6 py-10 sm:py-16">
    <PageHeader title="Lango Learn" description={`Welcome, ${name}.`} />
    <section className="mt-8 rounded-2xl border border-[var(--line-strong)] bg-[var(--panel-strong)] p-6 shadow-[var(--shadow-card)] sm:p-8" aria-labelledby="welcome-title">
      <p className="text-sm font-semibold uppercase tracking-widest text-[var(--accent-deep)]">Coming together</p>
      <h2 id="welcome-title" className="display-font mt-3 text-3xl font-semibold leading-tight sm:text-4xl">Learn at your own pace.</h2>
      <p className="mt-4 leading-7 text-[var(--muted)]">We’re preparing original, reviewed courses. There are no published course lessons to start yet.</p>
    </section>
    <ImportPanel userId={userId} />
  </div>
}

function GuestAbout({ signIn }: { signIn: () => void }) { return <GuestFrame signIn={signIn}><About /></GuestFrame> }
function About() {
  return <div className="mx-auto w-full max-w-3xl py-8">
    <PageHeader title="About Lango Learn" description="Our approach to the first course." />
    <div className="mt-8 space-y-5 leading-7 text-[var(--muted)]">
      <p>Lango Learn is being designed around a small, carefully reviewed first course. Lessons will connect practical goals with useful feedback and opportunities to revisit what you’ve learned.</p>
      <p>We’re still choosing and preparing that course. The two word guest sample is local practice, not a published course lesson.</p>
    </div>
  </div>
}
