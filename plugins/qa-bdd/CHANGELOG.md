# Changelog

All notable changes to the qa-bdd plugin are documented here.

## 0.3.0

### Added

- **`--filter-names` option for `inspect-steps`.** `inspect_bdd_steps.py` now
  accepts `--filter-names <file>` to scope inspection to a set of function names
  (one per line; blank lines and `#` comments ignored), and reports any names not
  found in the suite. Lets a step-assertion audit target a specific subset of steps
  instead of always scanning the whole suite.
