#!/usr/bin/env bash
#
# merge-survey.sh — Phases 1-2 of the semantic-merge skill: map the branch DAG and
# size the TRUE conflict surface (via merge-tree simulation) BEFORE any merge, so you
# plan against real conflicts, not the inflated "files touched by both" count.
#
# Usage:
#   merge-survey.sh <branch-a> <branch-b> [<branch-c> ...] [--onto <base>]
#
#   --onto <base>   integration base to measure "behind" against (default: origin/main)
#
# Read-only: runs no merge, touches no working tree. Requires git >= 2.38 for merge-tree.
#
set -euo pipefail

BASE_REF="origin/main"
BRANCHES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --onto) BASE_REF="$2"; shift 2;;
    *) BRANCHES+=("$1"); shift;;
  esac
done

[ "${#BRANCHES[@]}" -ge 2 ] || { echo "usage: merge-survey.sh <branch-a> <branch-b> [...] [--onto <base>]" >&2; exit 1; }
git rev-parse --verify -q "$BASE_REF" >/dev/null || { echo "merge-survey: base ref '$BASE_REF' not found" >&2; exit 1; }
for b in "${BRANCHES[@]}"; do
  git rev-parse --verify -q "$b" >/dev/null || { echo "merge-survey: branch '$b' not found" >&2; exit 1; }
done

rule() { printf '%s\n' "────────────────────────────────────────────────────────"; }

echo "Integration base: $BASE_REF"
rule
echo "PER-BRANCH vs base:"
for b in "${BRANCHES[@]}"; do
  ahead="$(git rev-list --count "$BASE_REF..$b")"
  behind="$(git rev-list --count "$b..$BASE_REF")"
  printf "  %-45s +%-5s ahead  -%-5s behind\n" "$b" "$ahead" "$behind"
done

rule
echo "PAIRWISE relationship + TRUE conflict surface:"
n=${#BRANCHES[@]}
for ((i=0;i<n;i++)); do
  for ((j=i+1;j<n;j++)); do
    A="${BRANCHES[$i]}"; B="${BRANCHES[$j]}"
    mb="$(git merge-base "$A" "$B")"
    echo
    echo "  $A  <->  $B"
    if git merge-base --is-ancestor "$A" "$B" 2>/dev/null; then
      echo "    LINEAR: $A is an ancestor of $B (B already contains A) — trivial merge"
      continue
    fi
    if git merge-base --is-ancestor "$B" "$A" 2>/dev/null; then
      echo "    LINEAR: $B is an ancestor of $A (A already contains B) — trivial merge"
      continue
    fi
    echo "    DIVERGENT  merge-base=${mb:0:9}"
    # symmetric difference: commits on one side not the other. NOT merge-base..X,
    # which overcounts shared commits when the DAG has cross-merges between A and B.
    printf "      unique to %s: %s commits\n" "$A" "$(git rev-list --count "$B..$A")"
    printf "      unique to %s: %s commits\n" "$B" "$(git rev-list --count "$A..$B")"

    # TRUE conflict surface — simulate the merge, list only actually-conflicting files.
    conflicts="$(git merge-tree --write-tree --name-only "$A" "$B" 2>/dev/null | tail -n +2 | sed '/^$/,$d' || true)"
    if [ -z "$conflicts" ]; then
      echo "      conflicts: NONE (textually clean — still run the coherence gate)"
      continue
    fi
    echo "      conflicts ($(printf '%s\n' "$conflicts" | grep -c .)):"
    # classify: mechanical (rule-resolved) vs semantic (needs a per-file resolver)
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      case "$f" in
        *.lock|*-lock.yaml|*lock.json|*baseline*|*.duplication-baseline|*.type-ignore-baseline|\
        *known_failures*|*allowlist*|*.jsonl|*.db|*migration-hint*|*.lock.*|*.snap|*.pyi)
          printf "        [mechanical] %s\n" "$f";;
        *)
          printf "        [semantic ] %s\n" "$f";;
      esac
    done <<< "$conflicts"
  done
done

rule
echo "Next: merge in a worktree (Phase 3), resolve [mechanical] by rule and spawn one"
echo "resolver subagent per [semantic] file (Phase 5), then run the coherence gate (Phase 7)."
