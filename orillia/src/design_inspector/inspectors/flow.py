from __future__ import annotations

import os

from nova_act import SecurityOptions
from nova_act.asyncio import NovaAct as AsyncNovaAct

from design_inspector.schemas import FlowEvaluation, FlowStep


def _security_options_for(url: str) -> SecurityOptions | None:
    if url.startswith("file://"):
        path = url.removeprefix("file://")
        directory = os.path.dirname(path)
        return SecurityOptions(allowed_file_open_paths=[f"{directory}/*"])
    return None


FLOW_STEP_PROMPT = """\
You just arrived on this web page. Evaluate it as if you are a real user navigating this site for the first time.

Consider:
- Is the page's purpose immediately clear?
- Do you know what you're supposed to do here?
- Does this page feel like a natural continuation from where you came from?
- Are the navigation options clear and consistent with previous pages?
- Would a computer use agent (an AI that navigates websites) be able to understand what to do here?

Provide your evaluation as a first impression."""


NAVIGATE_PROMPT = """\
Look at the navigation links on this page. Click on a link that takes you to a different \
page on this same website that you have NOT visited yet. Prefer main navigation links \
(like Pricing, Sign Up, Dashboard) over footer links. \
If you have already visited all the linked pages, or there are no more internal links, do nothing."""


FLOW_EVALUATION_PROMPT = """\
You have just navigated through a multi-page website, visiting several pages in sequence.
Now evaluate the site as a whole — how well do the pages connect as a collective experience?

Consider:
- Navigation coherence: Do menus, labels, and link text stay consistent across pages?
- Dead ends: Were there pages where you had no clear next action?
- Confusing transitions: Did any page feel jarring or disconnected from the previous one?
- Information architecture: Are pages organized logically? Does the site tell a coherent story?
- Agent navigability: Could an AI agent reliably traverse this site and understand the page relationships?

Be specific and concrete in your critique. Name exact pages, elements, and inconsistencies."""


async def run_flow_inspection(
    url: str,
    *,
    max_depth: int = 3,
    output_dir: str = "/tmp/design-inspector",
) -> FlowEvaluation:
    os.makedirs(output_dir, exist_ok=True)

    nova_kwargs: dict = {"starting_page": url, "headless": True}
    security = _security_options_for(url)
    if security:
        nova_kwargs["security_options"] = security

    steps: list[FlowStep] = []

    async with AsyncNovaAct(**nova_kwargs) as nova:
        # Evaluate the starting page
        step_result = await nova.act_get(
            FLOW_STEP_PROMPT,
            schema=FlowStep.model_json_schema(),
        )
        step = FlowStep.model_validate(step_result.parsed_response)
        step.page_url = url
        step.arrived_from = None
        step.navigation_element_used = None
        steps.append(step)

        # Navigate through the site by clicking links
        for i in range(max_depth - 1):
            prev_url = str(nova.page.url)

            # Ask Nova Act to click a navigation link
            nav_result = await nova.act(NAVIGATE_PROMPT)

            current_url = str(nova.page.url)

            # If we didn't navigate anywhere, we're done
            if current_url == prev_url:
                break

            # Evaluate this new page
            step_result = await nova.act_get(
                FLOW_STEP_PROMPT,
                schema=FlowStep.model_json_schema(),
            )
            step = FlowStep.model_validate(step_result.parsed_response)
            step.page_url = current_url
            step.arrived_from = prev_url
            steps.append(step)

        # Final holistic evaluation after having navigated the whole site
        evaluation_result = await nova.act_get(
            FLOW_EVALUATION_PROMPT,
            schema=FlowEvaluation.model_json_schema(),
        )
        evaluation = FlowEvaluation.model_validate(evaluation_result.parsed_response)

    evaluation.steps = steps
    return evaluation
