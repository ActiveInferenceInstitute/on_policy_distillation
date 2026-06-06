The `manuscript_staleness` fragment closes the hydration loop. `output/reports/manuscript_staleness_report.json` checks {{manuscript_staleness_row_count}} manuscript token bindings against the current generated variables after resolved markdown is written; the pass flag is `{{manuscript_staleness_all_fresh}}`.

`output/reports/manuscript_hardcoded_variable_audit.json` then scans the source fragments for guarded generated values that appear as prose literals instead of double-brace manuscript-variable placeholders. It guards {{hardcoded_variable_guarded_count}} formatted token values and records {{hardcoded_variable_issue_count}} hard-coded-value issues; the pass flag is `{{hardcoded_variables_all_auto_injected}}`.

This is a publication-systems claim, not a domain result. A stale hydrated value, unresolved token, hard-coded generated value, or missing resolved section becomes a validation failure before PDF or web outputs are accepted.
