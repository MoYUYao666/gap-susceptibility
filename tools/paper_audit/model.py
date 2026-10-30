# -*- coding: utf-8 -*-
"""Data model for the paper-audit mode (English-only artifact).

Severity policy
---------------
P0  blocker   : the manuscript cannot be submitted / would be rejected or retracted
P1  major     : a reader, editor or reviewer can see the defect; must fix before submission
P2  minor     : quality / consistency issue; fix when feasible
P3  info      : informational; record only

Status
------
PASS / FAIL / WARN / SKIP / MANUAL / ERROR
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    MANUAL = "MANUAL"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Check:
    id: str
    dimension: str
    severity: Severity
    title: str
    method: str
    automated: bool = True


@dataclass
class Finding:
    check_id: str
    dimension: str
    severity: Severity
    title: str
    status: Status
    message: str = ""
    evidence: str = ""
    remediation: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["status"] = self.status.value
        return d


@dataclass
class Report:
    profile: str
    profile_label: str
    manuscript: str
    generated_at: str
    git_commit: str
    git_branch: str
    git_dirty: bool
    audit_id: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    commands: list[str] = field(default_factory=list)

    # -- aggregation -----------------------------------------------------
    def by_status(self, status: Status) -> list[Finding]:
        return [f for f in self.findings if f.status == status]

    def counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in Status}
        for f in self.findings:
            out[f.status.value] += 1
        return out

    def gate_failures(self) -> list[Finding]:
        """P0/P1 failures plus any ERROR (an ERROR is a toolkit defect)."""
        blocked = []
        for f in self.findings:
            if f.status == Status.ERROR:
                blocked.append(f)
            elif f.severity in (Severity.P0, Severity.P1) and f.status == Status.FAIL:
                blocked.append(f)
        return blocked

    def verdict(self) -> str:
        if self.gate_failures():
            return "BLOCKED"
        p2 = [f for f in self.findings if f.severity == Severity.P2 and f.status == Status.FAIL]
        if p2:
            return "READY-WITH-MINOR"
        return "READY"

    def grade(self) -> str:
        v = self.verdict()
        if v == "BLOCKED":
            return "D"
        if v == "READY-WITH-MINOR":
            return "B"
        return "A"

    def as_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "profile": self.profile,
            "profile_label": self.profile_label,
            "manuscript": self.manuscript,
            "generated_at": self.generated_at,
            "git_commit": self.git_commit,
            "git_branch": self.git_branch,
            "git_dirty": self.git_dirty,
            "verdict": self.verdict(),
            "grade": self.grade(),
            "counts": self.counts(),
            "environment": self.environment,
            "commands": self.commands,
            "artifacts": self.artifacts,
            "findings": [f.as_dict() for f in self.findings],
            "checks": [asdict(c) | {"severity": c.severity.value} for c in self.checks],
        }
