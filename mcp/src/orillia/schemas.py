from __future__ import annotations

from pydantic import BaseModel, Field


# --- Flow Evaluation ---


class FlowStep(BaseModel):
    """A single page visited during flow navigation."""

    page_url: str = Field(description="The URL of the page visited")
    page_title: str = Field(description="The visible page title or heading")
    arrived_from: str | None = Field(
        default=None, description="URL of the page we navigated from, or null if starting page"
    )
    navigation_element_used: str | None = Field(
        default=None,
        description="Description of the link/button clicked to arrive here (e.g. 'Pricing nav link')",
    )
    first_impression: str = Field(
        description="What a user would think/feel upon landing on this page. Is the purpose clear?"
    )
    clarity_score: int = Field(
        ge=1, le=10, description="How clear is this page's purpose and what to do next (1=confusing, 10=crystal clear)"
    )


class FlowEvaluation(BaseModel):
    """Evaluation of how pages connect as a collective experience."""

    steps: list[FlowStep] = Field(description="Pages visited in navigation order")
    dead_ends: list[str] = Field(
        description="Pages where the user has no clear next action or way to continue"
    )
    confusing_transitions: list[str] = Field(
        description="Page transitions that feel jarring, illogical, or break the user's mental model"
    )
    navigation_consistency: str = Field(
        description="Assessment of whether navigation elements (menus, breadcrumbs) stay consistent across pages"
    )
    information_architecture_score: int = Field(
        ge=1, le=10, description="How well the site's pages are organized and interconnected (1=chaotic, 10=intuitive)"
    )
    overall_coherence: str = Field(
        description="Does the site tell a coherent story? Do pages build on each other logically?"
    )


# --- Tension Points ---


class TensionPoint(BaseModel):
    """A specific friction point that would confuse humans or agents."""

    location: str = Field(description="Where on the page this issue exists (e.g. 'hero section, primary CTA button')")
    description: str = Field(description="What the problem is, described concretely")
    who_it_affects: str = Field(
        description="Who is impacted: 'humans', 'agents', or 'both' — and why each group struggles"
    )
    severity: str = Field(description="'critical' (blocks progress), 'warning' (causes confusion), or 'info' (suboptimal)")
    what_should_change: str = Field(
        description="Specific, actionable instruction for what should be different (not code — design intent)"
    )
    why_it_matters: str = Field(
        description="The consequence of not fixing this — what goes wrong for users or agents"
    )


class TensionReport(BaseModel):
    """Report of friction points found on a page."""

    url: str
    tension_points: list[TensionPoint] = Field(description="All friction points identified")
    patterns_observed: list[str] = Field(
        description="Recurring design anti-patterns across the page (e.g. 'inconsistent button styles')"
    )
    agent_navigability_score: int = Field(
        ge=1, le=10, description="How easily a computer use agent could navigate this page (1=impossible, 10=trivial)"
    )
    human_usability_score: int = Field(
        ge=1, le=10, description="How easily a human could accomplish their goal on this page (1=frustrating, 10=delightful)"
    )


# --- Segment Evaluation ---


class SegmentEvaluation(BaseModel):
    """Evaluation of a site from a specific user segment's perspective."""

    segment_name: str = Field(description="The user segment evaluated (e.g. 'new_user', 'ai_agent')")
    url: str
    can_complete_primary_task: bool = Field(
        description="Whether this user segment could accomplish the site's primary intended action"
    )
    primary_task_description: str = Field(
        description="What the evaluator interpreted as the site's primary intended action for this segment"
    )
    confusion_points: list[str] = Field(
        description="Specific moments where this user segment would feel lost or uncertain"
    )
    efficiency_score: int = Field(
        ge=1, le=10, description="How quickly this segment could accomplish their goal (1=extremely slow, 10=instant)"
    )
    onboarding_clarity: int = Field(
        ge=1, le=10, description="How clear the first-time experience is for this segment (1=opaque, 10=obvious)"
    )
    recommendations: list[str] = Field(
        description="Specific changes that would improve the experience for this segment"
    )


# --- Full Report ---


class FullReport(BaseModel):
    """Comprehensive design evaluation combining flow, tension, and segment analyses."""

    url: str
    timestamp: str
    flow: FlowEvaluation
    tensions: TensionReport
    segment_evaluations: list[SegmentEvaluation]
    overall_design_health: int = Field(
        ge=1, le=100, description="Composite score of the site's design quality (1=broken, 100=exemplary)"
    )
    top_priorities: list[str] = Field(
        description="Ranked list of the most impactful changes to make, starting with the most critical"
    )
    screenshot_paths: list[str] = Field(
        default_factory=list, description="File paths to screenshots captured during evaluation"
    )


# --- Training Data ---


class TrainingExample(BaseModel):
    """A single training example for computer use agent fine-tuning."""

    url: str
    segment: str = Field(description="User segment context (e.g. 'new_user', 'ai_agent')")
    navigation_step: str = Field(description="What navigation action was being attempted")
    observation: str = Field(description="What was observed about the design at this step")
    issue_category: str = Field(
        description="Category: flow, tension, accessibility, consistency, clarity, affordance"
    )
    severity: str = Field(description="critical, warning, or info")
    recommendation: str = Field(description="What should change and why")
