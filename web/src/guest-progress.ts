export const GUEST_KEY = 'lango-learn:guest-sample:v1'

export type GuestProgress = { id: string; completedSteps: number; savedAt: number; claimedBy?: string }

export function readGuestProgress(): GuestProgress | null {
  try {
    const raw = localStorage.getItem(GUEST_KEY)
    if (!raw) return null
    const value: unknown = JSON.parse(raw)
    if (!value || typeof value !== 'object') return null
    const row = value as Record<string, unknown>
    if (typeof row.id !== 'string' || !/^[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12}$/i.test(row.id)) return null
    if (!Number.isInteger(row.completedSteps) || Number(row.completedSteps) < 0 || Number(row.completedSteps) > 2) return null
    if (!Number.isInteger(row.savedAt) || Number(row.savedAt) < 0) return null
    if (row.claimedBy !== undefined && typeof row.claimedBy !== 'string') return null
    return row as GuestProgress
  } catch { return null }
}

export function saveGuestProgress(progress: GuestProgress): boolean {
  try { localStorage.setItem(GUEST_KEY, JSON.stringify(progress)); return true } catch { return false }
}

export function newGuestProgress(): GuestProgress {
  return { id: crypto.randomUUID(), completedSteps: 0, savedAt: Date.now() }
}
