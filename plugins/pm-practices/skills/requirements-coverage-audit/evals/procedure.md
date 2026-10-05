# Execute and grade coverage evaluations

Use this procedure when changing the skill. The JSON cases are evaluator inputs,
not runtime references for an ordinary SoW analysis. No evaluation framework is
required: the host assistant can run and grade isolated skill invocations.
See [results.md](results.md) for the pre-rename historical record and
[results-pm-275.md](results-pm-275.md) for the new run and its limits.

## Static checks

Resolve the installed skill-creator directory and record it with the result. Run
its validator against this skill directory, for example in the Codex environment:

```sh
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/requirements-coverage-audit
```

Use the real resolved paths, not the example paths above. Do not waive errors.
This skill stores version under metadata and documents arguments in Inputs to
match that validator, unlike plugins using top-level version. The validator
version used for implementation allows name, description, license, allowed-tools,
and metadata; it rejects top-level version, args, compatibility and description
angle brackets. Record validator changes if a later installation differs.

Check JSON syntax and local Markdown links. Inspect required instructions for
unfinished placeholders and fixed project/version/heading/milestone assumptions.
Project names in clearly marked evaluation cases are intentional; zero search
matches is not the criterion. The below-about-500-line entrypoint target is soft.

## Behavioral runs

1. Read evals.json as coordinator. Resolve public fixture paths relative to evals/
   and private input paths relative to the repository root. A case may instead
   point to a private case file; read its prompt, inputs and expectations there.
   Keep private documents and generated private reports outside git; never
   commit copies of drafts/.
   Missing private fixtures mean the private case is skipped, not passed. Synthetic
   cases are required and must pass. Record unvalidated criteria explicitly.
2. For each case create a fresh temporary directory (mktemp -d), containing only
   SKILL.md, its runtime references, that case's raw documents/export pages, and an output
   directory. Do not copy evals.json, this procedure, old assessment reports, or
   grader expectations into the executor's context. Source documents themselves
   remain complete. The maintainer-validation link need not resolve in this
   intentionally minimal execution copy; it is not a runtime dependency.
3. Give a fresh-context agent the case prompt, copied skill path, raw document
   paths, and output directory. Instruct it to read only these inputs and use
   apply_patch for report writes. Use one independent invocation per case; do
   not reuse a context across cases. Sequential execution inside a case is fine.
   If delegation is unavailable, use equivalent separate fresh host sessions and
   record that mechanism. Do not claim an independent eval from a context that
   has already read the expected answers.
4. Read the generated artifacts as grader and compare each expectation to source
   evidence, recording pass/fail plus report file and section. Evaluate meaning,
   not exact prose or regex matches. Read every inventory/ledger row and reconcile
   counts. For the private case, enumerate source capabilities and historical items against
   the submitted ledger; a polished report with an unsupported completeness
   assertion must fail. Old assessment reports may guide review, but their counts
   and judgments are not ground truth and never go to the executor.
5. Record date, executor mode, input hashes, validator path/result, per-case and
   per-expectation outcomes, output locations, and skipped/unvalidated criteria.
   Public synthetic outputs may be retained locally for inspection. A committed
   results note should contain outcomes/evidence anchors, not private document
   content. Mark temporary artifact locations as local and nonportable.
6. If a behavior fails, fix only the demonstrated cause and rerun affected cases
   in fresh contexts. Retain the failed outcome in the results note. Do not tune
   instructions to fixture names or pass by weakening the expectation.

## Recorded Jira cases

The synthetic pages use Jira REST v3 enhanced-search response envelopes, not a
made-up tracker schema. Snapshot notes are companion provenance, not extra API
fields. Complete cases supply both pages; incomplete cases supply only page 1
and explicit missing-page metadata. ADF descriptions retain paragraphs and lists.
Run each case independently; do not expose the withheld page to incomplete runs.
These checks prove export interpretation and missing-data handling, not live
pagination. ACLI help inspection is not live integration validation. Record live
retrieval as untested unless exercised against an authorized site.

Retain the pre-rename results without rewriting old outcomes as new passes.
Inspect shipped resources for real customer identifiers and credentials. Invented
fixture names/keys and example.invalid URLs are intentional, not configuration.
