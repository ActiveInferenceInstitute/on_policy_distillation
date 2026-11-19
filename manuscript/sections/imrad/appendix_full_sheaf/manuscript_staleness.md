The appendix `manuscript_staleness` row points to
`output/reports/manuscript_staleness_report.json`. It checks
{{manuscript_staleness_row_count}} token bindings after hydration, including late
audit variables, and the pass flag is `{{manuscript_staleness_all_fresh}}`.

The staleness report authenticates each occurrence's source identity, format,
and resolved span, plus complete canonical section content, including
token-free sections. Saved green flags do not substitute for current hydration
equality. Repeated occurrences and self-referential count/freshness tokens are
checked independently after genuine convergence.
