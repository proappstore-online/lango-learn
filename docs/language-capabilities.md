# Language capability contract

[`contracts/language-capabilities.json`](../contracts/language-capabilities.json) is the
versioned, machine-readable baseline for language-aware course and evaluator work.
Its four profiles are **illustrative fixtures**, not a supported-language list or
approved course pair. The [backlog](comprehensive-epics-and-issues.md) still
requires a declared source → target pair, a reviewed A0–early-A1 Latin-script
slice, original content, and a later course-style approval. Arabic is included
to keep the data model and tests from assuming every script is left-to-right.

Each profile records a BCP-47 language-region tag, ISO 15924 script code,
direction and input guidance, then explicit policies for tokenisation,
morphology, word order, punctuation, diacritics, transliteration, and regional
variants. `doNotNormalise` names distinctions that should never disappear in a
generic preprocessing pass. Each of the nine dimensions has a paired fixture
per profile. `distinct` means the examples must stay distinguishable;
`explicit_variant_only` means an editor may accept the alternative for a
specific exercise with a rationale, but the language profile alone does not
make it correct. A fixture is a policy example, not published lesson text.

## Evaluation boundary

The default is NFC Unicode normalization only. No case folding, whitespace
collapse, punctuation or diacritic stripping, transliteration, regional
substitution, morphology expansion, or word reordering is implied. Token
boundaries and accepted surface forms belong to reviewed content. A future
server-side evaluator (LNG-056) must use the course's pinned capability version
and authored variants, and the golden corpus (LNG-057) must cover accepted,
rejected, partial, regional, script, IME, and accessibility cases. The current
app has no evaluator; this registry does not grade learner answers.

When a language is proposed for launch, a qualified language reviewer should
confirm its profile, examples, dialect/orthography policy and input behavior.
Add or revise fixtures with the profile, record the chosen source and target
tags in the course release, and pin the contract schema/data version for
reproducible attempt review. A region tag in the registry never authorizes a
regional answer globally. For RTL content, render the target text with its
language tag and direction, and isolate it from surrounding UI; the direction
field is not an instruction to reverse token order.

`pnpm check:languages` validates the registry and its conservative defaults.
`pnpm test` also checks fixture coverage and detects weakened defaults, missing
cases, and incorrect RTL metadata. The validation is structural; linguistic
approval and the later evaluator corpus remain separate release gates.
