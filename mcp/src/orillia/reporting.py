from __future__ import annotations

import json
from datetime import datetime, timezone

from orillia.schemas import (
    FlowEvaluation,
    FullReport,
    SegmentEvaluation,
    TensionReport,
    TrainingExample,
)


def assemble_report(
    *,
    url: str,
    flow: FlowEvaluation,
    tensions: TensionReport,
    segment_evaluations: list[SegmentEvaluation],
) -> FullReport:
    # Compute overall design health from component scores
    scores = [
        flow.information_architecture_score * 10,  # scale 1-10 to 1-100
        tensions.agent_navigability_score * 10,
        tensions.human_usability_score * 10,
    ]
    for seg in segment_evaluations:
        scores.append(seg.efficiency_score * 10)
        scores.append(seg.onboarding_clarity * 10)

    overall = round(sum(scores) / len(scores)) if scores else 50

    # Build ranked priority list from critical/warning tension points
    priorities: list[str] = []
    for tp in sorted(tensions.tension_points, key=lambda t: _severity_rank(t.severity)):
        priorities.append(f"[{tp.severity.upper()}] {tp.location}: {tp.what_should_change}")

    # Add flow-level issues
    for dead_end in flow.dead_ends:
        priorities.append(f"[FLOW] Dead end: {dead_end}")
    for transition in flow.confusing_transitions:
        priorities.append(f"[FLOW] Confusing transition: {transition}")

    # Add segment-specific issues
    for seg in segment_evaluations:
        if not seg.can_complete_primary_task:
            priorities.insert(0, f"[CRITICAL] {seg.segment_name} cannot complete primary task: {seg.primary_task_description}")

    return FullReport(
        url=url,
        timestamp=datetime.now(timezone.utc).isoformat(),
        flow=flow,
        tensions=tensions,
        segment_evaluations=segment_evaluations,
        overall_design_health=max(1, min(100, overall)),
        top_priorities=priorities,
    )


def export_training_jsonl(report: FullReport, output_path: str) -> int:
    examples: list[TrainingExample] = []

    # Convert tension points to training examples
    for tp in report.tensions.tension_points:
        examples.append(TrainingExample(
            url=report.url,
            segment="general",
            navigation_step=f"Evaluating {tp.location}",
            observation=tp.description,
            issue_category=_categorize_tension(tp.description),
            severity=tp.severity,
            recommendation=tp.what_should_change,
        ))

    # Convert flow issues to training examples
    for dead_end in report.flow.dead_ends:
        examples.append(TrainingExample(
            url=report.url,
            segment="general",
            navigation_step="Flow navigation",
            observation=f"Dead end encountered: {dead_end}",
            issue_category="flow",
            severity="critical",
            recommendation=f"Provide clear next actions at: {dead_end}",
        ))

    for transition in report.flow.confusing_transitions:
        examples.append(TrainingExample(
            url=report.url,
            segment="general",
            navigation_step="Page transition",
            observation=f"Confusing transition: {transition}",
            issue_category="consistency",
            severity="warning",
            recommendation=f"Improve transition coherence: {transition}",
        ))

    # Convert segment findings to training examples
    for seg in report.segment_evaluations:
        for confusion in seg.confusion_points:
            examples.append(TrainingExample(
                url=report.url,
                segment=seg.segment_name,
                navigation_step="Segment evaluation",
                observation=confusion,
                issue_category="clarity",
                severity="warning",
                recommendation=next(
                    (r for r in seg.recommendations if _fuzzy_match(confusion, r)),
                    f"Address confusion point for {seg.segment_name}: {confusion}",
                ),
            ))

    with open(output_path, "w") as f:
        for example in examples:
            f.write(json.dumps(example.model_dump()) + "\n")

    return len(examples)


def _severity_rank(severity: str) -> int:
    return {"critical": 0, "warning": 1, "info": 2}.get(severity.lower(), 3)


def _categorize_tension(description: str) -> str:
    desc_lower = description.lower()
    if any(w in desc_lower for w in ["cta", "button", "click", "action"]):
        return "affordance"
    if any(w in desc_lower for w in ["nav", "menu", "link", "navigate"]):
        return "flow"
    if any(w in desc_lower for w in ["inconsist", "different", "mismatch", "conflict"]):
        return "consistency"
    if any(w in desc_lower for w in ["unclear", "confus", "ambig", "vague"]):
        return "clarity"
    if any(w in desc_lower for w in ["contrast", "color", "read", "visible"]):
        return "accessibility"
    return "tension"


def _fuzzy_match(a: str, b: str) -> bool:
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    return len(words_a & words_b) >= 3
