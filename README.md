**Simulation code for Paper 4B, "Defensive Tempo, Estate Structure and Collapse: Cyber-Risk Propagation on a Frozen Substrate" (CEMT programme).**
# PhDPaper4B v0.19

This release is the single-file, reproducible simulator behind every table in Paper 4B. It is self-contained (one Python file, numpy only) and carries the frozen propagation core embedded and hash-checked, so a reader can regenerate the paper's results from one command.

---

## Highlights

- One file, numpy only. No scipy, no scikit-learn, no external model code.
- The frozen core (cemt_core v0.8, set digest `97dbae47…`) is embedded and verified at load; a mismatch aborts the run.
- Every result in the paper regenerates from a single `--mode`, or from the interactive menu.
- Each run writes its seeds, full configuration and raw per-run outcomes, so every number is traceable.

---

## What is included

- `PhDPaper4B.py` — the simulator (v0.19).
- `percolation_4b.py` — standalone bond-percolation test (its logic is also built into the main file via `--mode percolation`).
- `RELEASE_NOTES.md` — this file.

Run outputs are not committed; they are produced locally under the run root (see below).

---

## Requirements

- Python 3.9 or later
- numpy

`pyyaml` is optional and only used by the Stage 0 scenario self-check. No other third-party packages are required.

---

## Quick start

Launch with no arguments for the interactive menu:

```
python PhDPaper4B.py
```

Or run a specific experiment from the command line:

```
python PhDPaper4B.py --mode paper        # the full evidence suite (E1-E5)
python PhDPaper4B.py --mode cusp         # the cusp test (E7)
python PhDPaper4B.py --mode blindtest    # the visibility-free lever (E6)
```

The banner should read `PhDPaper4B v0.19 (2026-10-09)` and report `frozen core 97dbae4714b2 verified: True`.

Run root resolves in this order: `--out-root`, then `$CEMT_RUNS`, then `C:\cemt_runs` on Windows or `~/cemt_runs` elsewhere. Results land in `<root>/4B/<timestamp>_p4b_<mode>_v0_19/`.

---

## Reproducing the paper

| Paper result | Command | Output |
|---|---|---|
| Full suite (E1-E5) | `--mode paper` | `P4B_PAPER.md` and subfolders |
| E1 transition / fold | `--mode all` | `fold/P4B_summary.md` |
| E2 tempo decomposition | `--mode twocad` | `twocad/P4B_twocad.md` |
| E3 hysteresis + bistability | (in `--mode paper`) | `hysteresis/P4B_hysteresis.md` |
| E4 robustness | `--mode robust` | `robust/P4B_robustness.md` |
| E5 epidemic + percolation | `--mode validate` | `reduction/reduction_test.json`, `reduction/percolation_test.json` |
| E6 blind-lever | `--mode blindtest` | `P4B_blindtest.md` |
| E7 cusp | `--mode cusp` | `P4B_cusp.md` |
| Order-sensitivity | `--mode ordertest` | `P4B_ordertest.md` |
| Frozen-core self-check | `--mode stage0` | console |

Confirmatory settings: n = 40 estate nodes, horizon 1000 ticks, 4 seed blocks x 100 runs per cell (400 independent runs per cell). On a 15-worker machine the full suite takes roughly 1.5 to 2 hours; the cusp and validation modes take minutes. Append `-pilot` to the suite, two-cadence, hysteresis, blindtest, ordertest or cusp modes for a fast reduced-scale smoke of the same pipeline.

---

## Outputs and provenance

Each run writes a timestamped folder containing:

- `run_record.json` — code and spec version, frozen-core digest and verification flag, seeds, estate size, horizon, runs per cell, and the full design.
- `per_run*.json` — the raw per-run outcomes behind every aggregated statistic.
- a `.csv` of the aggregated grid.
- a human-readable `P4B_*.md` summary.

Statistics are computed over independent runs: each of the 400 runs per cell uses a distinct seed that governs both the estate construction and the stochastic dynamics, so bootstrap intervals resample independent observations.

---

## Integrity

The propagation substrate (cemt_core v0.8) is embedded byte for byte, zlib-compressed and base64-encoded, and its set digest `97dbae47…` is checked at load. No node-level condition of the frozen core is modified by this file; all driver and engine logic (timing, blocking, reconfiguration, the blind lever, the acquisition-check order flag) sits above it.

---

## Scope and limitations

This is an exploratory, proof-of-principle study on synthetic estates. It characterises where collapse can occur and what shape it takes; it does not forecast incidents and is not fitted to incident data. The cusp (E7) is substantiated by a deterministic mean-field reduction and an ungated-recovery control, not by a full two-parameter bifurcation continuation of the stochastic model. The epidemic and percolation baselines (E5) are computed on separate stripped graphs and are contextual, compared on ordering rather than as a common critical point. See the paper's Limitations section for the full list.

---

## Changelog

- **v0.19** — Cusp test (`--mode cusp`): deterministic mean-field bifurcation map plus an ungated-recovery control.
- **v0.18** — Removed the scipy and scikit-learn dependencies; the logistic threshold fit and bimodality statistics are now pure numpy. numpy-only from here.
- **v0.17** — Sharpened the epidemic threshold (more realisations, bootstrap interval); E3 now reports the per-trajectory gap and switch-point distributions; added the acquisition-check order-sensitivity flag and test; added the blind-lever experiment.
- **v0.16** — Merged the bond-percolation test into the academic-theory validation.
- **v0.15** — Two-cadence confirmatory design (operational and structural tempo swept independently); paper-suite mode.
- **v0.14** — Austere time-and-adaptation baseline on the frozen core.

---

## Citation

If you use this code, please cite Paper 4B (CEMT programme). A full citation and DOI will be added here on publication.

## License

To be specified by the author before public release.
