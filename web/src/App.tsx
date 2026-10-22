import { initPro, ProShell, PageHeader, useAuth, type NavItem } from '@proappstore/sdk'

const app = initPro({ appId: 'lango-learn' })

const NAV: NavItem[] = [
  { label: 'Home', href: '/', title: 'Lango Learn' },
  { label: 'About', href: '/about', title: 'About — Lango Learn' },
]

export default function App() {
  return (
    <ProShell app={app} appName="Lango Learn" nav={NAV} branding="app">
      {window.location.pathname === '/about' ? <About /> : <Home />}
    </ProShell>
  )
}

function Home() {
  const { user } = useAuth()

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10 sm:py-16">
      <PageHeader
        title="Lango Learn"
        description={user ? `Welcome, ${user.name ?? 'learner'}.` : 'A home for thoughtful language practice.'}
      />
      <section className="mt-8 rounded-2xl border border-[var(--line-strong)] bg-[var(--panel-strong)] p-6 shadow-[var(--shadow-card)] sm:p-8" aria-labelledby="welcome-title">
        <p className="text-sm font-semibold uppercase tracking-widest text-[var(--accent-deep)]">Coming together</p>
        <h2 id="welcome-title" className="display-font mt-3 text-3xl font-semibold leading-tight sm:text-4xl">
          Learn at your own pace.
        </h2>
        <p className="mt-4 max-w-2xl leading-7 text-[var(--muted)]">
          We’re building original lessons with clear explanations and room to review.
          Courses are still being prepared, so there are no lessons to start yet.
        </p>
      </section>
      <p className="mt-6 text-sm leading-6 text-[var(--muted)]">
        Visit About to learn how we’re approaching the first course.
      </p>
    </div>
  )
}

function About() {
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10 sm:py-16">
      <PageHeader title="About Lango Learn" description="Our approach to the first course." />
      <div className="mt-8 space-y-5 leading-7 text-[var(--muted)]">
        <p>
          Lango Learn is being designed around a small, carefully reviewed first course.
          Lessons will connect practical goals with useful feedback and opportunities to revisit what you’ve learned.
        </p>
        <p>
          We’re still choosing and preparing that course. This early app shell lets us establish
          the platform and test the experience before learning content is available.
        </p>
      </div>
    </div>
  )
}
