---
name: semantic-merge
description: >
  Merge, consolidate, or integrate branches with per-file semantic conflict
  resolution and a behavior-level coherence gate. Use when asked to "semantic
  merge", "merge branches", "merge two branches", "consolidate branches",
  "integrate branches", "merge these PRs", "combine branches", "resolve merge
  conflicts", "reconcile branches", "rebase and resolve", or when a merge has
  large or divergent conflicts that textual auto-merge would silently mis-resolve.
  Maps the branch DAG, sizes the TRUE conflict surface, isolates in a worktree,
  splits conflicts into mechanical vs semantic, resolves each semantic file with a
  fresh-context subagent (union of intent), then verifies coherence with
  compile -> lint -> import-all -> behavior tests before committing.
args: <branch-a> <branch-b> [<branch-c> ...] [--onto <base>]
---

# Semantic Merge

Merge branches so the RESULT is correct, not merely conflict-free.

**Governing principle:** a textual auto-merge is not a correct merge. Git resolves
by lines; it silently mis-merges logic where both sides changed related code, and it
"cleanly" auto-merges files that are semantically broken. Every merge is verified at
the behavior layer, not the "no conflict markers" layer.

## Hard rules (non-negotiable)

- **Never content-merge generated or tool-owned data files.** Lockfiles
  (`*.lock`), dependency snapshots, generated code/stubs, database snapshots,
  task-tracker data (issue journals/DBs), migration-hint markers, and coverage/
  duplication baselines are NOT source. Pin them to ONE side (usually the target
  base) or regenerate them after the merge — never hand-splice their contents. For
  any data store shared across worktrees, a content merge causes real data loss:
  stop and ask if it is more than a trivial marker.
- **"Unit tests pass" is not "merge is correct."** The gate is import-all
  collection plus the behavior-level suite (integration / BDD / e2e). A merge can be
  unit-green and still broken across files.
- **A clean auto-merge still needs review.** Conflicts are the loud failures;
  mis-merges are the silent ones. Phase 6 exists for exactly this.
- **Isolate the work.** Never do a large/divergent merge in a dirty working tree —
  use a throwaway worktree so uncommitted changes and shared data stores are safe.

## Phase 1 — Map the DAG (before touching anything)

Do not merge blind. Establish the shape with `scripts/merge-survey.sh <A> <B> [--onto <base>]`,
or by hand:

```bash
git merge-base --is-ancestor A B      # is one branch already contained in the other?
BASE=$(git merge-base A B)
git rev-list --count $BASE..A         # commits unique to A
git rev-list --count $BASE..B         # commits unique to B
git rev-list --count A..<base>        # how far behind the integration base
```

- **Linear** (one contains the other) → the merge is trivial; just fast-forward / merge the superset.
- **Divergent** → the real work is only where the *unique* commits of each side overlap. The
  huge "files touched by both" number is mostly shared base history — ignore it.

## Phase 2 — Size the TRUE conflict surface

"Files changed by both branches" wildly overstates the work. Simulate the merge
without touching the tree:

```bash
git merge-tree --write-tree --name-only A B    # exit 1 + the ACTUALLY-conflicting files
```

This is what you plan against — often an order of magnitude smaller than the overlap
count. If it exits 0, the merge is textually clean (still run Phases 6–7).

## Phase 3 — Isolate in a worktree

```bash
git worktree add <path> -b <result-branch> <base>
cd <path>
```

Your primary working tree — uncommitted changes, shared data stores — is never at risk.

## Phase 4 — Merge in dependency order; triage each conflict into two buckets

Merge the smaller / base-most branch first, then the larger. On conflict, classify
EVERY conflicted file:

- **Mechanical** — baselines, ledgers, lockfiles, generated files, data markers.
  Resolve by *rule*, no judgment, and record the rule:
  - ratchet/coverage baselines → the higher value (or regenerate);
  - retired ledgers/allowlists → the side that owns that file's purpose;
  - lockfiles → regenerate from the merged manifest;
  - data/marker files → pin to base (Hard rules).
- **Semantic** — real source and tests. One fresh-context resolver subagent PER
  FILE (Phase 5).

## Phase 5 — Per-file semantic resolution (the core)

For each semantic conflict, spawn ONE subagent scoped to ONE file. Run them in
parallel (they touch disjoint files). Give each subagent this contract:

```
Resolve ONE merge conflict. Work ONLY on: <FILE>. Worktree: <path>.

This is a UNION merge — both branches' intent must survive unless one strictly
subsumes the other. Trace intent from all three stages before editing:
  git show :1:<FILE>   # base (common ancestor)
  git show :2:<FILE>   # OURS   (<what branch A does, one line>)
  git show :3:<FILE>   # THEIRS (<what branch B does, one line>)
  git log --oneline <branch> -- <FILE>   # why each side changed it

Resolve by preserving BOTH sides' behavior. If one side strictly subsumes the
other, take it and say why. Resolve against the MERGED TREE's actual state, not
either side alone — watch for a resolution that references a symbol the other side
deleted, or leaves a helper undefined that the already-merged body still calls.

Exit gate (must both hold):
  - the file compiles / type-checks (language-appropriate: py_compile, tsc --noEmit,
    cargo check, etc.);
  - `grep -nE '^(<<<<<<<|=======|>>>>>>>)' <FILE>` returns nothing.
Do NOT touch any other file. Do NOT git add or commit.
Return 2-4 sentences: what each side did and how you reconciled it.
```

If the project has purpose-built resolver/review agents, use those; otherwise
`general-purpose` with the contract above is correct.

## Phase 6 — Enumerate ALL diffs, not just the conflicts

The AUTO-merged files are the silent risk. Before trusting the result, classify every
`src/` diff of the merge result against each parent as intentional-or-accidental. At
minimum, let the Phase 7 gate catch cross-file breakage; for high-stakes merges,
diff-review the auto-merged core modules explicitly.

## Phase 7 — Coherence gate (behavior, not markers)

Cheapest-to-slowest; stop at the first failure and fix before proceeding:

1. **Compile / syntax** — every changed file, language-appropriate.
2. **Lint / static analysis** — catches undefined names and dropped imports (the
   classic "an agent kept the side whose helper the other side deleted").
3. **Import-all / test collection** — imports every module together
   (`pytest --collect-only`, a full type-check, or a build). This is the real
   cross-file coherence check that independent per-file resolutions passed but might
   contradict each other.
4. **Behavior suite** — integration / BDD / e2e, not just unit. This is the merge
   gate for any behavior change.

Green at layers 1–3 means the per-file resolutions are mutually consistent; layer 4
confirms behavior is preserved.

## Phase 8 — Commit, pin, push

```bash
# verify data/marker files match the intended (pinned) side
git diff --quiet <base> HEAD -- <data-paths> || git checkout <base> -- <data-paths>
git commit --no-edit -m "<subject>

Resolution ledger:
- mechanical: <files> -> <rule applied>
- semantic:   <files> -> union / <side> subsumes (why)"
git push -u <remote> <result-branch>
```

The commit message carries the **resolution ledger** — which files were mechanical
(and the rule) vs semantic (and union/subsume + why) — so every decision is auditable
in one place.

## Failure protocol

- Conflict in a data/marker file that is more than a trivial marker → STOP and ask
  the user; do not content-merge it.
- Phase 7 layer fails after resolution → the mis-merge is in a file changed by both
  sides; re-open that file's resolver with the failure as context. Do not disable the
  check or call the failure "pre-existing" without diffing the base's actual state.
- Merge is larger than expected (Phase 2 surface is huge) → surface the true conflict
  count and the DAG to the user and confirm the approach before resolving.
