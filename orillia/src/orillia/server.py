from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP

mcp = FastMCP(
    name="orillia",
    instructions=(
        "You are connected to Orillia. Use these tools to evaluate "
        "web design and UX quality from the perspective of both human users and computer use agents. "
        "These tools critique and diagnose — they never fix. Read the findings and decide what to do. "
        "Start with full_evaluation for a comprehensive audit, or use individual tools for targeted checks."
    ),
)

SEGMENT_TYPES = Literal["new_user", "power_user", "casual_user", "screen_reader", "ai_agent"]


@mcp.tool
async def evaluate_flow(url: str, max_depth: int = 3) -> dict:
    """Navigate a website starting from the given URL, follow links up to max_depth pages,
    and evaluate how pages connect as a collective experience.

    Reports on navigation coherence, dead ends, confusing transitions, and information architecture.
    Evaluates whether the site tells a coherent story as users move between pages.
    """
    from orillia.inspectors.flow import run_flow_inspection

    result = await run_flow_inspection(url, max_depth=max_depth)
    return result.model_dump()


@mcp.tool
async def find_tension_points(url: str) -> dict:
    """Identify specific friction points on a web page where a human user or computer use agent
    would get confused, stuck, or lost.

    Finds ambiguous CTAs, unclear element purposes, inconsistent patterns, missing affordances,
    and elements that would trip up both humans browsing and AI agents navigating programmatically.
    """
    from orillia.inspectors.tension import run_tension_inspection

    result = await run_tension_inspection(url)
    return result.model_dump()


@mcp.tool
async def evaluate_as_segment(url: str, segment: SEGMENT_TYPES = "new_user") -> dict:
    """Navigate and evaluate a website from a specific user segment's perspective.

    Segments:
    - new_user: First-time visitor. Evaluates onboarding clarity, discoverability, learning curve.
    - power_user: Experienced user seeking efficiency. Evaluates shortcuts, information density, workflow speed.
    - casual_user: Infrequent visitor on mobile. Evaluates simplicity, touch targets, cognitive load.
    - screen_reader: Assistive technology user. Evaluates semantic structure, ARIA labels, focus order.
    - ai_agent: Computer use agent navigating programmatically. Evaluates element clarity, predictable patterns, machine-parseability.
    """
    from orillia.inspectors.segments import run_segment_inspection

    result = await run_segment_inspection(url, segment=segment)
    return result.model_dump()


async def _run_full_evaluation(
    url: str,
    segments: list[str] | None = None,
    max_depth: int = 3,
) -> "FullReport":
    from orillia.inspectors.flow import run_flow_inspection
    from orillia.inspectors.segments import run_parallel_segment_inspections
    from orillia.inspectors.tension import run_tension_inspection
    from orillia.reporting import assemble_report

    segments = segments or ["new_user", "ai_agent"]

    flow = await run_flow_inspection(url, max_depth=max_depth)
    tensions = await run_tension_inspection(url)
    segment_results = await run_parallel_segment_inspections(url, segments=segments)

    return assemble_report(
        url=url,
        flow=flow,
        tensions=tensions,
        segment_evaluations=segment_results,
    )


@mcp.tool
async def full_evaluation(
    url: str,
    segments: list[str] | None = None,
    max_depth: int = 3,
) -> dict:
    """Run a comprehensive design evaluation: flow analysis + tension point detection + segment evaluations.

    This is the recommended starting point. It navigates the entire site, identifies UX issues,
    and evaluates from multiple user perspectives (default: new_user and ai_agent).

    Returns a complete report with ranked priorities, scores, and screenshot paths.
    """
    report = await _run_full_evaluation(url, segments=segments, max_depth=max_depth)
    return report.model_dump()


@mcp.tool
async def export_training_data(url: str, output_path: str = "./training_data.jsonl") -> dict:
    """Run a full evaluation and export findings as JSONL training data for improving computer use agent models.

    Each line in the JSONL contains a (url, segment, navigation_step, observation, issue_category,
    severity, recommendation) tuple that can be used for fine-tuning.
    """
    from orillia.reporting import export_training_jsonl

    report = await _run_full_evaluation(url)
    count = export_training_jsonl(report, output_path)
    return {"report": report.model_dump(), "training_data_path": output_path, "examples_exported": count}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
