# Account and guest sample (LNG-023)

The signed-out first lesson is an original, two-word Spanish greeting sample.
Its two-step checkpoint, random UUID, and browser timestamp are held only in
`localStorage` under `lango-learn:guest-sample:v1`. The app makes no lesson or
account action call before authentication. If storage is unavailable, the UI
says that the sample will be lost on navigation. Clearing browser data also
removes the local checkpoint. This sample is not a published course release,
graded result, or claim of mastery.

After PAS sign-in, the learner chooses **Save sample to my account**. The
authenticated `import_guest_lesson` batch validates the sample version,
checkpoint, timestamp and UUID; creates the caller's profile and default
preferences if needed; and records an immutable `guest_lesson_imports` row
owned by `:__user_id`. It never creates a `learning_sessions` or
`exercise_attempts` row. Client-reported completion and time are explicitly
unverified provenance; `created_at` is server time. The browser does not send
raw answers. The import ID is the guest session UUID, unique globally. A
second account cannot claim that ID, and a scoped receipt read reveals nothing
about the first account.

The browser retains the local copy until a scoped receipt confirms the import.
Retries reuse the same ID. If an existing receipt has different steps, the UI
reports the mismatch and leaves the local copy intact. A fresh sample generates
a new ID. A lower or equal checkpoint imported after another sample is stored
with `kept_existing`; the higher account checkpoint is not overwritten. The
summary action reports the caller's maximum imported step. A failed write or
receipt read leaves the local state available for retry. Batch execution is
atomic; malformed imports do not create an account profile. The UI marks a
confirmed local copy with the PAS user ID so another signed-in user of the same
browser is not offered that copy. That marker is a convenience, not an
authorization check; SQL ownership and the unique import ID are authoritative.

The regular learner actions still require a PAS session. When a real pilot
course is published, an explicit mapping and server evaluation policy will be
needed before this sample can count toward course progress. The import does not
silently claim equivalence to an authored lesson.
