# Audit: dot 2

| ID | severity | file:line | rule | evidence | why it matters | smallest fix |
|---|---|---|---|---|---|---|
| D2-01 | HIGH | `scripts/generate_txtp.py:124-131` | R6; success reporting | `result = subprocess.run(...)`; `if result.returncode != 0:` only prints a failure, then the loop continues and later prints completion. | A failed bank can leave missing `.txtp` output while the script still reports generation complete and exits normally. | Count failed banks and exit nonzero after processing if the count is nonzero. |
| D2-02 | HIGH | `scripts/generate_txtp.py:50-58, 65-68, 79-88, 99-107` | R6; stale output handling | Existing render-pool destinations are skipped with `if not os.path.exists(dest)`; the render pool is only created with `exist_ok=True`. | On reruns, old symlinks or copied files can remain in place and shadow changed inputs; no stale-entry warning is emitted. | Replace or validate an existing destination against its source before skipping it. |
| D2-03 | MED | `scripts/generate_txtp.py:40-43, 50-52, 65-68, 79-80, 133-135` | Deterministic ordering | These loops consume `os.listdir()` or `os.walk()` results without sorting; collected banks are then processed in that order. | Language discovery, bank processing, and crewvoice moves can vary across filesystems or runs. | Sort directory and filename lists before processing. |
| D2-04 | MED | `scripts/render_wav.py:41-44, 47-50` | Deterministic ordering | `.txtp` paths are appended directly from `os.walk()` and then passed to rendering without sorting. | With `--limit`, which files render can vary; concurrent execution order can also vary. | Sort `all_txtp` before filtering and applying the limit. |
| D2-05 | MED | `scripts/render_wav.py:30-37` | R6; dropped results | Once the “List of .txtp files missing source” header is seen, every later nonempty line is added to `missing_files`; no later-section boundary is recognized. | If the report has another section after this list, its lines may be mistaken for paths and silently filtered out. | Stop collecting when the missing-source section ends, according to the report format. |
| D2-06 | HIGH | `scripts/fix_random_container_render.py:75-97` | R6; cross-check claim | The docstring says “Uses BOTH methods and cross-checks”; code builds both `sids_noncomment` and `sids_comment`, but returns only `sorted(sids_noncomment)`. | A disagreement or missing WEM reference in either extraction method is not reported, so the decoder can silently omit a child SID. | Compare the two sets and raise or log their difference before returning. |
| D2-07 | HIGH | `scripts/fix_random_container_render.py:154-155` | R6; incomplete discovery | The scan loops over `os.listdir(args.txtp_dir)`, then only considers each direct child file. | `.txtp` files in nested directories are omitted. The other in-scope renderer explicitly discovers files recursively, so this can leave affected outputs uncorrected. | Walk the tree recursively and sort discovered `.txtp` paths. |
| D2-08 | LOW | `scripts/fix_random_container_render.py:51-70, 154-176` | Duplicated logic | `is_random_container_bug()` computes the group, Random mode, sound count, and Layer checks; `main()` repeats those checks inline. | The two implementations can drift and disagree about which files qualify. | Use `is_random_container_bug()` in the scan instead of repeating its predicate. |
| D2-09 | MED | `scripts/generate_txtp.py:9-12`; `scripts/render_wav.py:8-14`; `scripts/fix_random_container_render.py:132-149` | R11; hardcoded paths | CLI options have literal path defaults such as `input/WwiseSound`, `out_wwise/txtp`, `pool`, and `logs/...`. | Moving the project layout requires code-level defaults to be changed, and invocations that omit flags are tied to these paths. | Derive defaults from the project environment or require the corresponding CLI options. |

## Not verified

- Whether `report_dryrun.log` has further sections after the missing-source list; D2-05 is conditional on that format.
- Whether pre-existing render-pool entries or WAV outputs are stale in a real run; no pipeline command was run.
- Whether extracting the comment and non-comment SID forms should yield identical sets for actual `.txtp` files; the code does not perform the claimed comparison.
- WAAPI property writes and guessed property names: none appear in the three files read.
- Actual audio correctness and `vgmstream-cli` behavior: not exercised, as required.

## Files read

- `AGENTS.md`
- `scripts/generate_txtp.py`
- `scripts/render_wav.py`
- `scripts/fix_random_container_render.py`

## Summary

`generate_txtp.py` can report completion after bank failures and can reuse stale render-pool entries.
`render_wav.py` has filesystem-dependent ordering and may over-collect report lines as missing paths.
`fix_random_container_render.py` scans only its top directory and does not perform its documented SID cross-check.
No files were modified; this report is the only file created.
