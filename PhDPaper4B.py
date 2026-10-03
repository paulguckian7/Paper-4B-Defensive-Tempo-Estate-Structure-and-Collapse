# -*- coding: utf-8 -*-
"""
PhDPaper4B v0.9: Time and Adaptation on the frozen CEMT substrate.
======================================================================

One self-contained file. The frozen cemt_core v0.8 (set digest 97dbae47...) is
embedded byte for byte, zlib-compressed and base64-encoded, and hash-checked at
load; a mismatch aborts. No node-level IAE condition of the frozen core is
changed. What v0.9 adds is driver-level and engine-level: checking the
conditions takes time (the T1 Interface -> T2 Authority -> T3 Execution stage
sequence, one tick each), both actors act only through nodes they control, and
defence is reference-based blocking plus revoke / isolate / cut, not an external
reset. See Paper 4B Specification v1.5 and the build session of 1-2 Oct 2026.

Third-party libraries: numpy only (pyyaml only if STAGE0 reads scenario files).

Modes (python PhDPaper4B.py --mode MODE):
  stage0    reproduce the frozen v0.8 tier-1 reach and the E1/E2/E3 archetype
            signatures, if the scenario files are reachable (--scenarios DIR or
            auto-find). Self-verification of the frozen substrate.
  pilot     run the confirmatory-grid structures on the PILOT seeds, reduced,
            write a run directory with run_record.json and P4B_summary.md.
  all       the full grid on the confirmatory seeds.
  analyse   re-read a run directory and rewrite its summary.

Run root resolves in this order: --out-root, then $CEMT_RUNS, then
C:\\cemt_runs on Windows or ~/cemt_runs elsewhere; the paper subfolder 4B is
appended, so runs land in <root>/4B/<timestamp>_p4b_<mode>_v0_9/.
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import glob
import hashlib
import json
import os
import sys
import types
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

VERSION = "0.9"
CODE_VERSION = f"PhDPaper4B v{VERSION} (2026-10-02)"
SPEC_VERSION = "Paper 4B Specification v1.5: Time and Adaptation"


# ============================================================================
# Run-root resolution
# ============================================================================
def resolve_run_root(out_root: Optional[str] = None) -> str:
    if out_root:
        base = out_root
    elif os.environ.get("CEMT_RUNS"):
        base = os.environ["CEMT_RUNS"]
    elif sys.platform.startswith("win"):
        base = r"C:\cemt_runs"
    else:
        base = os.path.join(os.path.expanduser("~"), "cemt_runs")
    root = os.path.join(base, "4B")
    os.makedirs(root, exist_ok=True)
    return root


def new_run_dir(root: str, mode: str) -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    d = os.path.join(root, f"{stamp}_p4b_{mode}_v{VERSION.replace('.', '_')}")
    os.makedirs(d, exist_ok=True)
    return d


# ============================================================================
# EMBEDDED FROZEN CORE cemt_core v0.8 (hash-checked at load)
# ============================================================================

EMBEDDED_SET_DIGEST = '97dbae4714b278aa322588f69291cf10637fc1aaeedd434eb7590d9edbea3a09'
EMBEDDED_HASHES = {
    "spec": "4974b27b3a40166707878e31ea3b85e455ca0611738b80b86aea94d6f47576c9",
    "relations": "8757d456ad184634d635264dd7b2439a254353a442e7b5d3c1ffdb82ac32860e",
    "network": "49539f8a4670547ccea64cc389ba4fd54bd3c2c28ba2e6856fc583d5bb7172b4",
    "layers": "a0721d50c60de60fea958b796e412e4b89f839aa74321516029f62c342f581a4",
    "step": "6520b76ac28c6de6b98ff7ccf0e3379eb80dfc98d59d0b6460e0dbe7e423c7a6",
    "__init__": "68fb08d9ed682904cdf8614f7dce8153480b7da8b9d324dd578ca56cc896a3df"
}
EMBEDDED_SOURCES = {
    'spec': (
        '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'
        'eTKMoC+mBBSrOrqSa6VPVoLO/wF7Ko0e'
    ),
    'relations': (
        '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'
    ),
    'network': (
        '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'
        'Cov0lb25NYONnF+BkFRE32LeG+GXOjz4L+/R8qU='
    ),
    'layers': (
        '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'
    ),
    'step': (
        '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'
    ),
    '__init__': (
        'eNptUEFqwzAQvPsVi04JCBPaSyn0EIwphTYpSehVKPa4iMhas5JT2tfXduxTq9NoNDszWqVUUb6dqGLBIzXCPwgkaCAIFci1nUeL'
        'kGxyHKhhoXfbQeh+S6vrJr+jeIFH4rDOlVLZYNBSHjtU4yhLotWxQrDi+DiQmnZcQ9MBfjLU9MxXSLBDlqaCQ+0mOqO/Z5kpvI1R'
        '0yuu8Jq25xt7c/dsaxMnWPdtd4P/mY0PZixralel9dxb5oi4lF8yT/bsMYsC0hfLZZGce+drM5OaPhEgNmGKXtaR0C1y6YPhAJPE'
        '2aH+eI3zgjTFvm0HFIddVOMvXfNtKvbedhFZsT+U5qM8HF/2O3oitckfVPYLdfqVVA=='
    ),
}


# ============================================================================
# Embedded frozen core loader
# ============================================================================
def _load_embedded_core():
    """Decode, hash-check and execute the embedded cemt_core v0.8 modules,
    registering them in sys.modules as an in-memory package. Abort on mismatch."""
    try:
        import yaml  # noqa: F401
    except ImportError:
        stub = types.ModuleType("yaml")
        def _no_yaml(*a, **k):
            raise RuntimeError("PyYAML not installed; core YAML loaders unavailable")
        stub.safe_load = stub.safe_dump = stub.load = stub.dump = _no_yaml
        sys.modules["yaml"] = stub
    pkg = types.ModuleType("cemt_core")
    pkg.__path__ = []
    pkg.__package__ = "cemt_core"
    sys.modules["cemt_core"] = pkg
    report = {}
    for name in ("spec", "relations", "network", "layers", "step", "__init__"):
        src = zlib.decompress(base64.b64decode(EMBEDDED_SOURCES[name]))
        report[name] = hashlib.sha256(src).hexdigest() == EMBEDDED_HASHES[name]
        code = compile(src, f"<embedded cemt_core/{name}.py>", "exec")
        if name == "__init__":
            exec(code, pkg.__dict__)
            continue
        mod = types.ModuleType(f"cemt_core.{name}")
        mod.__package__ = "cemt_core"
        sys.modules[f"cemt_core.{name}"] = mod
        setattr(pkg, name, mod)
        exec(code, mod.__dict__)
    if not all(report.values()):
        bad = [k for k, v in report.items() if not v]
        raise SystemExit("EMBEDDED CORE DIFFERS from freeze record: " + ", ".join(bad)
                         + "; run not citable against the frozen substrate.")
    return pkg, report


_CORE_PKG, _FREEZE_REPORT = _load_embedded_core()

# NOTE: cemt_core is created in memory by _load_embedded_core() above; it is
# not a package on disk, so static analysers (Pylance/Pyright) will warn
# "Import could not be resolved". The import is correct at runtime. The
# pyright: ignore / type: ignore markers suppress that false positive.
from cemt_core.spec import (Condition, Governance, Node, Relation,  # type: ignore # noqa: E402
                            RelationClass, ScenarioSpec, RateSpec)
from cemt_core.network import build_network, NetworkState  # type: ignore # noqa: E402



# ---------------------------------------------------------------------------
# Stage constants
# ---------------------------------------------------------------------------
T1_INTERFACE = 1
T2_AUTHORITY = 2
T3_EXECUTION = 3
COMPROMISED = 4          # result state
RESIDENCE = 3            # ticks from admission to compromise when all checks pass


@dataclass
class Resident:
    """A payload in progress at a node: which stage it has reached, and its reference."""
    stage: int           # 1,2,3 = the stage whose check it must next pass
    reference: int       # campaign/version signature
    via: int             # supplier node index that delivered it
    needs: Tuple[str, ...] = ("X", "A")   # standing conditions still required


# Per-class standing conditions the RECEIVER must hold (the ones the relation
# does not itself supply), matching frozen v0.8 layer2 path_capability:
#   connection  supplies I  -> receiver needs standing X and A
#   channel     supplies I,X (route; X assessed on admission) -> needs A
#   directing   supplies I (plane must be owned) -> needs standing X and A
#   conferring  no push
CLASS_NEEDS = {
    RelationClass.CONNECTION: ("X", "A"),
    RelationClass.CHANNEL: ("A",),
    RelationClass.CONTROL_PLANE_DIRECTING: ("X", "A"),
}


@dataclass
class Config:
    # rhythms (ticks)
    horizon: int = 1000
    obs_interval: int = 5           # O: status-check cadence
    tactical_cycle: int = 5         # C_T: clean / isolate
    strategic_cycle: int = 20       # C_S: block push / cut  (H1 varies this)
    attacker_cycle: int = 5         # C_R
    block_delay: int = 2            # push lag added to the strategic boundary
    # doses (budget per cycle)
    def_tactical_budget: int = 1
    def_strategic_budget: int = 1
    atk_budget: int = 1
    # which defender rules are active
    defender_tactical: bool = True
    defender_strategic: bool = True
    strategic_revoke: bool = False   # v0.8 revoke_trust: disable an owned directing
                                     # plane whose member is observed compromised
    attacker_on: bool = True
    # observation latency to the master, in ticks, before it can detect a reference
    detect_latency: int = 1
    seed: int = 4101


@dataclass
class Record:
    tick: List[int] = field(default_factory=list)
    compromised: List[int] = field(default_factory=list)
    in_progress: List[int] = field(default_factory=list)
    isolated: List[int] = field(default_factory=list)
    master_held_by_attacker: List[int] = field(default_factory=list)
    n_blacklisted: List[int] = field(default_factory=list)
    n_references_live: List[int] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Engine4B:
    def __init__(self, spec: ScenarioSpec, cfg: Config,
                 master: Optional[str] = None,
                 source: Optional[str] = None,
                 source_trusted: bool = False,
                 deterministic: bool = False):
        self.cfg = cfg
        self.deterministic = deterministic or bool(getattr(spec, "deterministic", False))
        self.rng = np.random.default_rng(cfg.seed)
        self.net: NetworkState = build_network(spec, np.random.default_rng(cfg.seed))
        # directing control-plane ownership (a plane is owned once its controller
        # is compromised); mirrors frozen layer3.
        self.owned_plane: Dict[str, bool] = {g: False for g in self.net.control_planes}
        self.owned_at: Dict[str, int] = {}
        self.ever_seen_comp: Set[int] = set()
        n = self.net.N
        self.n = n
        self.master = self.net.index[master] if master else None
        self.source = self.net.index[source] if source else None
        self.source_trusted = source_trusted
        self.est = ~self.net.external

        # dynamic state
        self.state = np.zeros(n, dtype=np.int8)          # 0 healthy, COMPROMISED when fallen
        self.comp_ref = np.full(n, -1, dtype=int)        # reference held by a compromised node
        self.resident: Dict[int, Resident] = {}          # node -> in-progress payload
        self.isolated = np.zeros(n, dtype=bool)
        self.rel_enabled: Dict[RelationClass, np.ndarray] = {
            rc: self.net.access[rc].copy() for rc in RelationClass
        }
        # adjacency lists per class (supplier -> set of receivers), maintained
        # on disable, so propagation does not recompute flatnonzero every tick
        self.adj: Dict[RelationClass, Dict[int, Set[int]]] = {}
        for rc in RelationClass:
            d: Dict[int, Set[int]] = {}
            rows, cols = np.nonzero(self.rel_enabled[rc])
            for i_, j_ in zip(rows.tolist(), cols.tolist()):
                d.setdefault(i_, set()).add(j_)
            self.adj[rc] = d
        # directing-plane lookup: (controller, member) -> group, built once
        self.plane_of: Dict[Tuple[int, int], str] = {}
        for g, (ctl, members) in self.net.control_planes.items():
            for m in members:
                self.plane_of[(int(ctl), int(m))] = g
        self.blacklist: Dict[int, Set[int]] = {j: set() for j in range(n)}   # per-node refs denied
        self.pending_blocks: List[Tuple[int, int]] = []  # (arrival_tick, reference) fleet pushes
        self.attacker_owns_master = False
        self.atk_reference = 0                           # current campaign reference
        self._next_ref = 1
        self.first_seen_ref: Dict[int, int] = {}         # reference -> tick master could first see it
        self.rec = Record()

        # authority revoked on nodes (condition removal): blocks T2 structurally
        self.authority_revoked = np.zeros(n, dtype=bool)
        # hardened: interface/execution removed
        self.iface_removed = np.zeros(n, dtype=bool)
        self.exec_removed = np.zeros(n, dtype=bool)

    # ---- helpers ----------------------------------------------------------
    def _has_I(self, j: int) -> bool:
        return bool(self.net.sup_I[j]) and not self.iface_removed[j]

    def _has_X(self, j: int) -> bool:
        return bool(self.net.sup_X[j]) and not self.exec_removed[j]

    def _has_A(self, j: int) -> bool:
        return bool(self.net.sup_A[j]) and not self.authority_revoked[j]

    def _compromised_mask(self) -> np.ndarray:
        return self.state == COMPROMISED

    def _source_reference(self, tick: int) -> int:
        """A trusted source mints a new reference every update (strategic) cycle, free."""
        if not self.source_trusted:
            return self.atk_reference
        version = tick // max(1, self.cfg.strategic_cycle)
        ref = 10_000 + version
        self.first_seen_ref.setdefault(ref, tick)
        return ref

    # ---- propagation (one tick) ------------------------------------------
    def _update_plane_ownership(self, tick: int):
        """A directing plane is owned once its controller is compromised
        (mirrors frozen layer3; member-takeover is stochastic, out of Stage 0).
        Records the tick ownership began, for rollout-delay honouring."""
        for g, (ctl, members) in self.net.control_planes.items():
            if not self.owned_plane.get(g, False) and self.state[ctl] == COMPROMISED:
                self.owned_plane[g] = True
                self.owned_at[g] = tick

    def _rollout_ready(self, g: str, j: int, tick: int) -> bool:
        """Honour the directing plane's rollout schedule (frozen layer2): a member
        is pushed only once ticks-since-ownership exceeds its delay. No schedule
        means immediate."""
        delays = self.net.rollout_delays.get(g, {})
        if not delays:
            return True
        since = tick - self.owned_at.get(g, tick)
        return since >= delays.get(int(j), 0) + 1

    def _needs_met(self, j: int, needs: Tuple[str, ...]) -> bool:
        ok = True
        if "X" in needs:
            ok = ok and self._has_X(j)
        if "A" in needs:
            ok = ok and self._has_A(j)
        if "I" in needs:
            ok = ok and self._has_I(j)
        return ok

    def _plane_group_of(self, i: int, j: int) -> Optional[str]:
        return self.plane_of.get((i, j))

    def _disable_relation(self, rc: RelationClass, i: int, j: int):
        """Disable one relation and keep the adjacency list in step."""
        if self.rel_enabled[rc][i, j]:
            self.rel_enabled[rc][i, j] = False
            s = self.adj[rc].get(i)
            if s is not None:
                s.discard(j)

    def _deliver(self, tick: int):
        """Compromised, non-isolated nodes (and a persistent source) deliver on
        enabled relations. A delivery of class rc creates or advances a resident
        payload at the receiver, which must still pass the standing conditions rc
        does not supply (CLASS_NEEDS), spread over the stage ticks. Uses the
        maintained adjacency lists so it does not scan the matrix each tick."""
        self._update_plane_ownership(tick)

        def _offer(i: int, j: int, rc: RelationClass, ref: int):
            if self.state[j] == COMPROMISED or self.isolated[j]:
                return
            if rc == RelationClass.CONTROL_PLANE_CONFERRING:
                return  # conferring plane makes no push
            if rc == RelationClass.CONTROL_PLANE_DIRECTING:
                g = self.plane_of.get((i, j))
                if g is None or not self.owned_plane.get(g, False):
                    return  # plane not owned -> no directing push
                if not self._rollout_ready(g, j, tick):
                    return  # member not yet in the rollout window
            self._arrive(j, ref, i, rc, tick)

        comp_idx = np.flatnonzero(self.state == COMPROMISED)
        for i in comp_idx.tolist():
            if i == self.source or self.isolated[i]:
                continue  # source delivers only via its own block (rotating ref)
            ref = int(self.comp_ref[i]) if self.comp_ref[i] >= 0 else self.atk_reference
            for rc in RelationClass:
                for j in self.adj[rc].get(i, ()):  # maintained adjacency
                    _offer(i, j, rc, ref)

        if self.source is not None and not self.isolated[self.source]:
            sref = self._source_reference(tick)
            for rc in RelationClass:
                for j in list(self.adj[rc].get(self.source, ())):
                    _offer(self.source, j, rc, sref)

    def _arrive(self, j: int, ref: int, via: int, rc: RelationClass, tick: int):
        """Create or advance a resident payload at node j for class rc."""
        res = self.resident.get(j)
        if res is None or res.reference != ref:
            res = Resident(stage=T1_INTERFACE, reference=ref, via=via)
            res.needs = CLASS_NEEDS[rc]
            self.resident[j] = res
        else:
            # keep the least demanding admissible path seen this campaign
            if len(CLASS_NEEDS[rc]) < len(getattr(res, "needs", ("X", "A"))):
                res.needs = CLASS_NEEDS[rc]

    def _advance_residents(self, tick: int):
        """Each resident attempts its current stage check this tick. Stages take
        one tick each; checks for conditions the delivering class did not supply.
        T2 consults the blacklist (the block lands here)."""
        done = []
        for j, res in list(self.resident.items()):
            if self.isolated[j] or self.state[j] == COMPROMISED:
                done.append(j)
                continue
            needs = getattr(res, "needs", ("X", "A"))
            if res.stage == T1_INTERFACE:
                # admission: the delivering relation supplies reach; a fresh draw
                # each tick (faithful to v0.8 per-step redraw), certain if det.
                if self._admit(j):
                    res.stage = T2_AUTHORITY
            elif res.stage == T2_AUTHORITY:
                if res.reference in self.blacklist[j]:
                    continue  # blocked reference: Authority denies; stays resident
                if ("A" not in needs) or self._has_A(j):
                    res.stage = T3_EXECUTION
                elif not self._has_A(j):
                    done.append(j)  # authority structurally absent: cannot complete
            elif res.stage == T3_EXECUTION:
                if ("X" not in needs) or self._has_X(j):
                    if self._execute(j):
                        self.state[j] = COMPROMISED
                        self.comp_ref[j] = res.reference
                        done.append(j)
                else:
                    done.append(j)  # execution pathway absent
        for j in done:
            self.resident.pop(j, None)

    def _admit(self, j: int) -> bool:
        if self.deterministic:
            return True
        p = float(self.net.x_prob[j] * self.net.a_prob[j])
        return bool(self.rng.random() < min(max(p, 0.0), 1.0))

    def _execute(self, j: int) -> bool:
        return True  # given admission and authority, execution is deterministic

    # ---- super-node push --------------------------------------------------
    def _master_push(self, tick: int):
        """If the attacker owns the master, its directing authority pushes the
        campaign reference to all members (admitted certain)."""
        if self.master is None or not self.attacker_owns_master:
            return
        for rc in (RelationClass.CONTROL_PLANE_DIRECTING,):
            for j in np.flatnonzero(self.net.access[rc][self.master]):
                j = int(j)
                if self.state[j] == COMPROMISED or self.isolated[j]:
                    continue
                # certain admission; still subject to blacklist at T2
                if self.atk_reference in self.blacklist[j]:
                    continue
                self.state[j] = COMPROMISED
                self.comp_ref[j] = self.atk_reference

    # ---- defender actions -------------------------------------------------
    def _observe(self) -> np.ndarray:
        comp = self._compromised_mask()
        return comp & self.net.visible & self.est & ~self.isolated

    def _tactical(self, tick: int):
        obs = self._observe()
        budget = self.cfg.def_tactical_budget
        # clean highest-degree compromised first
        order = sorted(np.flatnonzero(obs), key=lambda j: -int(self.rel_enabled[RelationClass.CONNECTION][j].sum()))
        for j in order:
            if budget <= 0:
                break
            self.state[j] = 0
            self.comp_ref[j] = -1
            self.resident.pop(j, None)
            budget -= 1

    def _note_observed(self):
        """Latch nodes ever observed compromised (the defender remembers)."""
        for j in np.flatnonzero(self._observe()):
            self.ever_seen_comp.add(int(j))

    def _revoke_trust(self, tick: int):
        """v0.8 revoke_trust: for any owned directing plane with an observed
        compromised member, disable that plane's directing relations (the plane
        ceases to supply I / direct A), so a persistent controller can no longer
        re-deliver. Does not require the management master; the defender acts on
        planes inside its estate. Budget: one unit per plane revoked."""
        budget = self.cfg.def_strategic_budget
        for g, (ctl, members) in self.net.control_planes.items():
            if budget <= 0:
                break
            mem_idx = [int(m) for m in members]
            seen = any(m in self.ever_seen_comp for m in mem_idx)
            if self.owned_plane.get(g, False) and seen:
                # disable this controller's directing relations to its members
                for m in mem_idx:
                    self._disable_relation(RelationClass.CONTROL_PLANE_DIRECTING, int(ctl), m)
                self.owned_plane[g] = False
                budget -= 1

    def _strategic(self, tick: int):
        """Master detects references of observed compromises and schedules a
        fleet-wide block after block_delay; also may cut a source relation."""
        if self.cfg.strategic_revoke:
            self._revoke_trust(tick)
        if self.master is None:
            return
        # master must not itself be attacker-held to push defensive blocks
        if self.state[self.master] == COMPROMISED:
            return
        obs = self._observe()
        budget = self.cfg.def_strategic_budget
        refs_seen = {int(self.comp_ref[j]) for j in np.flatnonzero(obs) if self.comp_ref[j] >= 0}
        for ref in sorted(refs_seen):
            if budget <= 0:
                break
            self.pending_blocks.append((tick + self.cfg.block_delay, ref))
            budget -= 1
        # with remaining budget, cut a relation from a persistent source if known
        if budget > 0 and self.source is not None:
            for rc in RelationClass:
                live = sorted(self.adj[rc].get(self.source, ()))
                if live:
                    self._disable_relation(rc, int(self.source), int(live[0]))
                    budget -= 1
                    break

    def _apply_pending_blocks(self, tick: int):
        due = [(t, r) for (t, r) in self.pending_blocks if t <= tick]
        self.pending_blocks = [(t, r) for (t, r) in self.pending_blocks if t > tick]
        for _, ref in due:
            for j in range(self.n):
                self.blacklist[j].add(ref)

    # ---- attacker actions -------------------------------------------------
    def _attacker(self, tick: int):
        # take the master if a compromised node has authority over it
        if self.master is not None and not self.attacker_owns_master:
            if self.state[self.master] == COMPROMISED:
                self.attacker_owns_master = True
        # re-tool if the current campaign reference is broadly blacklisted
        blocked_everywhere = all(self.atk_reference in self.blacklist[j]
                                 for j in np.flatnonzero(self._compromised_mask())) \
            if self._compromised_mask().any() else False
        if blocked_everywhere:
            self.atk_reference = self._next_ref
            self._next_ref += 1
            self.first_seen_ref.setdefault(self.atk_reference, tick)
            # existing footholds adopt the new reference
            self.comp_ref[self._compromised_mask()] = self.atk_reference

    # ---- main loop --------------------------------------------------------
    def seed_entry(self, node: str, reference: int = 0):
        j = self.net.index[node]
        self.state[j] = COMPROMISED
        self.comp_ref[j] = reference
        self.atk_reference = reference
        self.first_seen_ref[reference] = 0

    def run(self) -> Record:
        cfg = self.cfg
        for tick in range(1, cfg.horizon + 1):
            # 1 propagation
            self._deliver(tick)
            self._advance_residents(tick)
            self._master_push(tick)
            # 2 blocks that come due
            self._apply_pending_blocks(tick)
            # 3 defender: strategic (block / revoke / cut) before tactical clean,
            # so revoke sees a compromise before cleaning removes it this tick
            self._note_observed()
            if cfg.defender_strategic and tick % cfg.strategic_cycle == 0:
                self._strategic(tick)
            if cfg.defender_tactical and tick % cfg.tactical_cycle == 0:
                self._tactical(tick)
            # 4 attacker
            if cfg.attacker_on and tick % cfg.attacker_cycle == 0:
                self._attacker(tick)
            # 5 record
            self._record(tick)
        return self.rec

    def _record(self, tick: int):
        comp = int((self._compromised_mask() & self.est).sum())
        self.rec.tick.append(tick)
        self.rec.compromised.append(comp)
        self.rec.in_progress.append(len(self.resident))
        self.rec.isolated.append(int(self.isolated.sum()))
        self.rec.master_held_by_attacker.append(int(self.attacker_owns_master))
        self.rec.n_blacklisted.append(len(self.blacklist[0]))
        self.rec.n_references_live.append(len({int(r) for r in self.comp_ref if r >= 0}))


# ---------------------------------------------------------------------------
# Structure builders (representative family + management super node)
# ---------------------------------------------------------------------------

def _gov():
    return [Governance("estate", True), Governance("vendor", False)]


def _node(nid, gov="estate", I=True, X=True, A=True, visible=True):
    return Node(id=nid, governance=gov, interface=bool(I),
                execution_pathway=bool(X), authority=bool(A), visible=visible)


def _rates():
    return RateSpec(threat_capability=1.0, authority_rate=0.9, execution_rate=0.9,
                    control_variance=0.0)


def build_chain(n_estate: int, with_master: bool, source: bool, seed: int):
    nodes = [_node(f"n{k}") for k in range(n_estate)]
    rels = []
    for k in range(n_estate - 1):
        rels.append(Relation(f"n{k}", f"n{k+1}", Condition.INTERFACE, RelationClass.CONNECTION))
    src = None
    if source:
        nodes.append(Node(id="src", governance="vendor", interface=True,
                          execution_pathway=True, authority=True, visible=False))
        rels.append(Relation("src", "n0", Condition.INTERFACE, RelationClass.CONNECTION))
        src = "src"
    master = None
    if with_master:
        nodes.append(_node("master", visible=True))
        for k in range(n_estate):
            rels.append(Relation("master", f"n{k}", Condition.AUTHORITY,
                                 RelationClass.CONTROL_PLANE_DIRECTING,
                                 conferral=True, group="mgmt"))
        master = "master"
    spec = ScenarioSpec(id="chain", description="4B chain", governance=_gov(),
                        nodes=nodes, relations=rels, seed=seed, deterministic=False)
    return spec, master, src


def build_star(n_estate: int, with_master: bool, source: bool, seed: int):
    # hub plus leaves; hub is a directing control plane over leaves
    nodes = [_node("hub")] + [_node(f"n{k}") for k in range(n_estate - 1)]
    rels = []
    for k in range(n_estate - 1):
        rels.append(Relation("hub", f"n{k}", Condition.AUTHORITY,
                             RelationClass.CONTROL_PLANE_DIRECTING, conferral=True, group="hub"))
    src = None
    if source:
        nodes.append(Node(id="src", governance="vendor", interface=True,
                          execution_pathway=True, authority=True, visible=False))
        rels.append(Relation("src", "n0", Condition.INTERFACE, RelationClass.CONNECTION))
        src = "src"
    master = None
    if with_master:
        nodes.append(_node("master", visible=True))
        for nd in ["hub"] + [f"n{k}" for k in range(n_estate - 1)]:
            rels.append(Relation("master", nd, Condition.AUTHORITY,
                                 RelationClass.CONTROL_PLANE_DIRECTING, conferral=True, group="mgmt"))
        master = "master"
    spec = ScenarioSpec(id="star", description="4B star", governance=_gov(),
                        nodes=nodes, relations=rels, seed=seed, deterministic=False)
    return spec, master, src


def build_mesh(n_estate: int, degree: int, with_master: bool, source: bool, seed: int):
    rng = np.random.default_rng(seed)
    nodes = [_node(f"n{k}") for k in range(n_estate)]
    rels = []
    seen = set()
    for a in range(n_estate):
        for _ in range(degree // 2):
            b = int(rng.integers(0, n_estate))
            if b == a or (a, b) in seen or (b, a) in seen:
                continue
            seen.add((a, b))
            rels.append(Relation(f"n{a}", f"n{b}", Condition.INTERFACE, RelationClass.CONNECTION))
    src = None
    if source:
        nodes.append(Node(id="src", governance="vendor", interface=True,
                          execution_pathway=True, authority=True, visible=False))
        rels.append(Relation("src", "n0", Condition.INTERFACE, RelationClass.CONNECTION))
        src = "src"
    master = None
    if with_master:
        nodes.append(_node("master", visible=True))
        for k in range(n_estate):
            rels.append(Relation("master", f"n{k}", Condition.AUTHORITY,
                                 RelationClass.CONTROL_PLANE_DIRECTING, conferral=True, group="mgmt"))
        master = "master"
    spec = ScenarioSpec(id="mesh", description="4B mesh", governance=_gov(),
                        nodes=nodes, relations=rels, seed=seed, deterministic=False)
    return spec, master, src


# ============================================================================
# Experiment driver: the confirmatory grid, pilot and full
# ============================================================================
DESIGN = dict(
    pilot_seeds=[231, 543, 311],
    confirmatory_seeds=[4101, 4201, 4202, 4301],
    structures=["mesh", "star", "chain"],
    actors=["defender", "attacker", "both"],
    doses=["none", "minor", "major"],
    strategic_cadence=[20, 80],          # H1: fast vs slow strategic cycle
    n_estate=dict(pilot=20, full=40),
    mesh_degree=6,
    runs_per_cell=dict(pilot=10, full=100),
    horizon=dict(pilot=300, full=1000),
    source_trusted=True,                 # persistent re-tooling vendor (SolarWinds-style)
)


def _build(structure, n_estate, seed):
    if structure == "chain":
        return build_chain(n_estate, with_master=True, source=True, seed=seed)
    if structure == "star":
        return build_star(n_estate, with_master=True, source=True, seed=seed)
    return build_mesh(n_estate, DESIGN["mesh_degree"], with_master=True, source=True, seed=seed)


def _cfg_for(actor, dose, cadence, horizon, seed):
    tac = dose if dose != "none" else 0
    budget = {"none": 0, "minor": 1, "major": 5}[dose]
    defender_on = actor in ("defender", "both") and dose != "none"
    attacker_on = actor in ("attacker", "both")
    return Config(
        horizon=horizon, obs_interval=5, tactical_cycle=5,
        strategic_cycle=cadence, attacker_cycle=5, block_delay=2,
        def_tactical_budget=budget, def_strategic_budget=budget, atk_budget=budget,
        defender_tactical=defender_on, defender_strategic=defender_on,
        strategic_revoke=defender_on, attacker_on=attacker_on, seed=seed,
    )


def _measures(rec, est_n):
    comp = np.array(rec.compromised, dtype=float)
    peak = comp.max() / max(est_n, 1)
    final = comp[-1] / max(est_n, 1)
    K = min(50, len(comp))
    tail_active = [c + p for c, p in zip(rec.compromised[-K:], rec.in_progress[-K:])]
    sustained_clean = all(a == 0 for a in tail_active)
    cumulative = comp.sum() / (max(est_n, 1) * len(comp))
    return dict(peak=peak, final=final, sustained_clean=sustained_clean, cumulative=cumulative)


def _cell_tasks(mode: str):
    """Enumerate the independent grid cells as picklable task tuples."""
    which = "pilot" if mode == "pilot" else "full"
    seeds = DESIGN["pilot_seeds"] if which == "pilot" else DESIGN["confirmatory_seeds"]
    n_estate = DESIGN["n_estate"][which]
    horizon = DESIGN["horizon"][which]
    R = DESIGN["runs_per_cell"][which]
    tasks = []
    for structure in DESIGN["structures"]:
        for actor in DESIGN["actors"]:
            cadences = DESIGN["strategic_cadence"] if actor != "attacker" else [DESIGN["strategic_cadence"][0]]
            for dose in DESIGN["doses"]:
                for cadence in cadences:
                    tasks.append((structure, actor, dose, cadence,
                                  tuple(seeds), n_estate, horizon, R,
                                  DESIGN["source_trusted"]))
    return tasks, (n_estate, horizon, R, seeds)


def _run_cell(task):
    """Run every seed x run for one grid cell and return its aggregated row.
    Top-level so it is picklable for multiprocessing (Windows spawn-safe)."""
    structure, actor, dose, cadence, seeds, n_estate, horizon, R, src_trusted = task
    cell = []
    for seed in seeds:
        for r in range(R):
            rseed = seed * 1000 + r
            spec, master, src = _build(structure, n_estate, rseed)
            spec.deterministic = False
            cfg = _cfg_for(actor, dose, cadence, horizon, rseed)
            eng = Engine4B(spec, cfg, master=master, source=src, source_trusted=src_trusted)
            for j in np.flatnonzero(eng.net.external):
                eng.state[j] = COMPROMISED
                eng.comp_ref[j] = 0
            eng.atk_reference = 0
            cell.append(_measures(eng.run(), int(eng.est.sum())))
    agg = {k: float(np.mean([c[k] for c in cell])) for k in ("peak", "final", "cumulative")}
    agg["sustained_clean_rate"] = float(np.mean([c["sustained_clean"] for c in cell]))
    return dict(structure=structure, actor=actor, dose=dose,
                strategic_cadence=cadence, n=len(cell), **agg)


def _sort_rows(rows):
    order_s = {s: i for i, s in enumerate(DESIGN["structures"])}
    order_a = {a: i for i, a in enumerate(DESIGN["actors"])}
    order_d = {d: i for i, d in enumerate(DESIGN["doses"])}
    return sorted(rows, key=lambda r: (order_s[r["structure"]], order_a[r["actor"]],
                                       order_d[r["dose"]], r["strategic_cadence"]))


def run_grid(mode: str, workers: int = 1):
    tasks, (n_estate, horizon, R, seeds) = _cell_tasks(mode)
    total = len(tasks)
    print(f"grid: {total} cells, {len(seeds)} seeds x {R} runs each, "
          f"n={n_estate}, horizon={horizon}, workers={workers}", flush=True)
    rows = []
    done = 0
    t_start = _dt.datetime.now()

    def _progress(row):
        nonlocal done
        done += 1
        elapsed = (_dt.datetime.now() - t_start).total_seconds()
        eta = elapsed / done * (total - done)
        print(f"  [{done:2d}/{total}] {row['structure']:5s} {row['actor']:8s} "
              f"{row['dose']:5s} C_S={row['strategic_cadence']:<3d} "
              f"peak={row['peak']:.2f} final={row['final']:.2f} "
              f"(elapsed {elapsed/60:.1f} min, ETA {eta/60:.1f} min)", flush=True)

    if workers and workers > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_run_cell, t) for t in tasks]
            for fut in as_completed(futs):
                row = fut.result()
                rows.append(row)
                _progress(row)
    else:
        for t in tasks:
            row = _run_cell(t)
            rows.append(row)
            _progress(row)
    return _sort_rows(rows)


def write_run(run_dir: str, mode: str, rows: list):
    import csv
    seeds = DESIGN["pilot_seeds"] if mode == "pilot" else DESIGN["confirmatory_seeds"]
    which = "pilot" if mode == "pilot" else "full"
    record = dict(
        code_version=CODE_VERSION, spec_version=SPEC_VERSION,
        frozen_core_digest=EMBEDDED_SET_DIGEST, frozen_core_verified=all(_FREEZE_REPORT.values()),
        mode=mode, created_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        seeds=seeds, n_estate=DESIGN["n_estate"][which], horizon=DESIGN["horizon"][which],
        runs_per_cell=DESIGN["runs_per_cell"][which], design=DESIGN,
    )
    with open(os.path.join(run_dir, "run_record.json"), "w") as f:
        json.dump(record, f, indent=2, default=str)
    cols = ["structure", "actor", "dose", "strategic_cadence", "n",
            "peak", "final", "cumulative", "sustained_clean_rate"]
    with open(os.path.join(run_dir, "grid.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    _write_summary(run_dir, mode, rows)


def _write_summary(run_dir: str, mode: str, rows: list):
    lines = [f"# Paper 4B {mode} run ({CODE_VERSION})", "",
             f"Frozen core digest: {EMBEDDED_SET_DIGEST[:12]} (verified: {all(_FREEZE_REPORT.values())})", "",
             "Peak compromised share by cell (mean over seeds x runs):", ""]
    lines.append("| structure | actor | dose | C_S | peak | final | sustained_clean |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['structure']} | {r['actor']} | {r['dose']} | {r['strategic_cadence']} "
                     f"| {r['peak']:.2f} | {r['final']:.2f} | {r['sustained_clean_rate']:.2f} |")
    # a couple of headline reads
    lines += ["", "## Quick reads", ""]
    def cell(structure, actor, dose, cs):
        for r in rows:
            if (r["structure"], r["actor"], r["dose"], r["strategic_cadence"]) == (structure, actor, dose, cs):
                return r
        return None
    for structure in DESIGN["structures"]:
        fast = cell(structure, "both", "major", 20)
        slow = cell(structure, "both", "major", 80)
        if fast and slow:
            lines.append(f"- {structure}: H1 cadence, peak fast(C_S=20)={fast['peak']:.2f} "
                         f"vs slow(C_S=80)={slow['peak']:.2f} (expect fast lower)")
    with open(os.path.join(run_dir, "P4B_summary.md"), "w") as f:
        f.write("\n".join(lines))


def analyse(run_dir: str):
    rec_path = os.path.join(run_dir, "run_record.json")
    if not os.path.exists(rec_path):
        raise SystemExit(f"no run_record.json in {run_dir}")
    import csv
    rows = []
    with open(os.path.join(run_dir, "grid.csv")) as f:
        for d in csv.DictReader(f):
            for k in ("peak", "final", "cumulative", "sustained_clean_rate"):
                d[k] = float(d[k])
            d["strategic_cadence"] = int(d["strategic_cadence"])
            rows.append(d)
    _write_summary(run_dir, "reanalyse", rows)
    print(f"rewrote summary in {run_dir}")


# ============================================================================
# STAGE0 self-verification (best-effort: needs the scenario files)
# ============================================================================
def _find_scenarios(explicit: Optional[str], out_root: Optional[str] = None):
    """Locate the scenarios folder (the one containing tier1/ and archetypes/).
    Order: --scenarios, then direct candidates beside the script and under the
    run root, then a recursive walk of the script dir and the run root so a
    nested cemt_core/scenarios is still found."""
    cands = [explicit] if explicit else []
    here = os.path.dirname(os.path.abspath(__file__))
    run_root = resolve_run_root(out_root)          # e.g. C:\cemt_runs\4B (created)
    run_base = os.path.dirname(run_root)           # e.g. C:\cemt_runs
    direct = [here, os.path.dirname(here), run_root, run_base,
              os.path.join(here, "cemt_core"), os.path.join(run_root, "cemt_core")]
    for base in direct:
        cands.append(os.path.join(base, "scenarios"))
    for c in cands:
        if c and glob.glob(os.path.join(c, "tier1", "c*.yaml")):
            return c
    # recursive fallback: walk the script dir and the run root for a tier1 set
    for walk_root in (here, run_root, run_base):
        if not os.path.isdir(walk_root):
            continue
        for root, _dirs, files in os.walk(walk_root):
            if root.replace("\\", "/").endswith("/tier1") and \
               any(f.startswith("c") and f.endswith(".yaml") for f in files):
                return os.path.dirname(root)   # the scenarios/ folder
    return None


def stage0(scenarios: Optional[str], out_root: Optional[str] = None):
    sdir = _find_scenarios(scenarios, out_root)
    if not sdir:
        root = resolve_run_root(out_root)
        print("STAGE0: scenario files not found. Put the 'scenarios' folder "
              f"(with tier1/ and archetypes/) under {root} or beside this file, "
              "or pass --scenarios DIR. Skipping.")
        return
    from cemt_core.spec import load_spec  # type: ignore
    from cemt_core.step import run_one_trial  # type: ignore
    tier1 = sorted(glob.glob(os.path.join(sdir, "tier1", "c*.yaml")))
    npass = 0
    for p in tier1:
        spec = load_spec(p); spec.deterministic = True
        net = build_network(spec, np.random.default_rng(spec.seed or 1))
        ref = {n for n in run_one_trial(net, np.random.default_rng(spec.seed or 1))["reached_set"]
               if not net.external[net.index[n]]}
        eng = Engine4B(spec, Config(horizon=200, defender_tactical=False,
                                    defender_strategic=False, attacker_on=False,
                                    seed=spec.seed or 1), deterministic=True)
        if spec.entry_node is not None:
            eng.seed_entry(spec.entry_node, 0)
        else:
            for j in np.flatnonzero(eng.net.external & eng.net.interface):
                eng.state[j] = COMPROMISED; eng.comp_ref[j] = 0
            eng.atk_reference = 0
        eng.run()
        got = {eng.net.ids[k] for k in np.flatnonzero(eng.state == COMPROMISED) if eng.est[k]}
        npass += (ref == got)
    print(f"STAGE0 tier-1 reach: {npass}/{len(tier1)}")


# ============================================================================
# Dispatch helpers (shared by the CLI and the interactive menu)
# ============================================================================
def _default_workers():
    try:
        return max(1, (os.cpu_count() or 2) - 1)
    except Exception:
        return 1


def _run_mode(mode: str, out_root=None, scenarios=None, run_dir=None, workers=None):
    if mode == "stage0":
        stage0(scenarios, out_root)
        return
    if mode == "analyse":
        if not run_dir:
            print("analyse needs a run directory.")
            return
        analyse(run_dir)
        return
    if workers is None:
        workers = _default_workers()
    root = resolve_run_root(out_root)
    rd = new_run_dir(root, mode)
    print(f"run dir: {rd}")
    t0 = _dt.datetime.now()
    rows = run_grid(mode, workers=workers)
    write_run(rd, mode, rows)
    dt = (_dt.datetime.now() - t0).total_seconds()
    print(f"{mode} complete in {dt:.0f}s; {len(rows)} cells; "
          f"see P4B_summary.md and grid.csv in the run dir")


def _list_runs(out_root=None):
    root = resolve_run_root(out_root)
    runs = sorted(glob.glob(os.path.join(root, "*_p4b_*")))
    return [r for r in runs if os.path.isdir(r)]


def menu(out_root=None, workers=None):
    """Interactive menu, shown when the file is launched with no arguments
    (e.g. double-clicked). Stays open until Quit, so the window does not flash."""
    root = resolve_run_root(out_root)
    if workers is None:
        workers = _default_workers()
    while True:
        print("\n" + "=" * 56)
        print(f"  {CODE_VERSION}")
        print(f"  frozen core {EMBEDDED_SET_DIGEST[:12]} verified: "
              f"{all(_FREEZE_REPORT.values())}")
        print(f"  run root: {root}")
        print(f"  workers: {workers} of {os.cpu_count()} cores")
        print("=" * 56)
        print("  1. Verify the model (Stage 0: tier-1 reach 20/20)")
        print("  2. Pilot run      (~1 min; writes a run folder)")
        print("  3. Full run       (confirmatory seeds; much longer)")
        print("  4. Re-analyse an existing run")
        print("  5. Quit")
        try:
            choice = input("\n  Choose 1-5: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            _run_mode("stage0", out_root)
        elif choice == "2":
            _run_mode("pilot", out_root, workers=workers)
        elif choice == "3":
            confirm = input("  Full run can take a while. Proceed? (y/N): ").strip().lower()
            if confirm == "y":
                _run_mode("all", out_root, workers=workers)
        elif choice == "4":
            runs = _list_runs(out_root)
            if not runs:
                print("  No runs found yet. Do a pilot or full run first.")
                continue
            for i, r in enumerate(runs[-15:], 1):
                print(f"    {i}. {os.path.basename(r)}")
            sel = input("  Run number to re-analyse: ").strip()
            try:
                _run_mode("analyse", out_root, run_dir=runs[-15:][int(sel) - 1])
            except (ValueError, IndexError):
                print("  Not a valid selection.")
        elif choice == "5":
            return
        else:
            print("  Please enter 1, 2, 3, 4 or 5.")


# ============================================================================
# CLI
# ============================================================================
def main(argv=None):
    # No arguments at all (e.g. double-clicked in Explorer) -> interactive menu.
    if argv is None and len(sys.argv) == 1:
        menu()
        return
    ap = argparse.ArgumentParser(description=CODE_VERSION)
    ap.add_argument("--menu", action="store_true", help="force the interactive menu")
    ap.add_argument("--mode", default="stage0",
                    choices=["stage0", "pilot", "all", "analyse"])
    ap.add_argument("--out-root", default=None,
                    help="run-root base; else $CEMT_RUNS, else C:/cemt_runs or ~/cemt_runs")
    ap.add_argument("--scenarios", default=None,
                    help="stage0: folder containing tier1/ and archetypes/")
    ap.add_argument("--run-dir", default=None, help="analyse: existing run directory")
    ap.add_argument("--workers", type=int, default=None,
                    help="parallel worker processes (default: CPU cores - 1; 1 = serial)")
    args = ap.parse_args(argv)

    print(CODE_VERSION)
    print(f"frozen core {EMBEDDED_SET_DIGEST[:12]} verified: {all(_FREEZE_REPORT.values())}")

    if args.menu:
        menu(args.out_root, args.workers)
        return
    _run_mode(args.mode, args.out_root, args.scenarios, args.run_dir, args.workers)


if __name__ == "__main__":
    main()