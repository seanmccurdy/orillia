from __future__ import annotations

import asyncio
import os

from nova_act import SecurityOptions
from nova_act.asyncio import NovaAct as AsyncNovaAct

from design_inspector.schemas import SegmentEvaluation


def _security_options_for(url: str) -> SecurityOptions | None:
    if url.startswith("file://"):
        path = url.removeprefix("file://")
        directory = os.path.dirname(path)
        return SecurityOptions(allowed_file_open_paths=[f"{directory}/*"])
    return None


SEGMENT_CONFIGS: dict[str, dict] = {
    "new_user": {
        "prompt": (
            "You are a first-time visitor who has never heard of this product. You landed here "
            "from a Google search. Navigate the site and evaluate:\n"
            "- Is it immediately clear what this product does and who it's for?\n"
            "- Can you figure out how to get started without any prior knowledge?\n"
            "- Is the onboarding path obvious — do you know what steps to take?\n"
            "- Are there any moments where you feel lost, confused, or unsure what to do next?\n"
            "- How much jargon or assumed knowledge is there?\n"
            "Try to sign up or start using the product. Note every point where you hesitate."
        ),
        "screen_width": 1440,
        "screen_height": 900,
    },
    "power_user": {
        "prompt": (
            "You are an experienced user who has used this product daily for months. You know "
            "exactly what you want to do and you want to do it fast. Navigate the site and evaluate:\n"
            "- Can you quickly find the feature or setting you need?\n"
            "- Are there keyboard shortcuts, search, or quick-access patterns?\n"
            "- Is information density appropriate — enough detail without clutter?\n"
            "- Are there unnecessary steps or confirmations that slow you down?\n"
            "- Can you accomplish your goal in the minimum number of clicks?\n"
            "Try to navigate to settings, find a specific project, and check billing."
        ),
        "screen_width": 1920,
        "screen_height": 1080,
    },
    "casual_user": {
        "prompt": (
            "You are a casual user on a mobile phone, checking in occasionally. You have limited "
            "attention and might be multitasking. Navigate the site and evaluate:\n"
            "- Are touch targets large enough to tap accurately?\n"
            "- Is the most important information visible without scrolling?\n"
            "- Can you accomplish your main task quickly before getting distracted?\n"
            "- Is the text readable at mobile size without zooming?\n"
            "- Are there any elements that don't work well on a small screen?\n"
            "Try to check the status of a project and view recent activity."
        ),
        "screen_width": 375,
        "screen_height": 812,
    },
    "screen_reader": {
        "prompt": (
            "You are using a screen reader to navigate this site. Evaluate the semantic structure:\n"
            "- Are headings properly nested (h1 > h2 > h3)?\n"
            "- Do images have alt text? Do icons have accessible labels?\n"
            "- Is the tab order logical — can you navigate linearly and understand the page?\n"
            "- Are form fields properly labeled?\n"
            "- Are interactive elements (buttons, links) distinguishable from static content?\n"
            "- Are there any content areas that would be invisible or confusing to a screen reader?\n"
            "Navigate through the page as if reading it linearly, noting semantic issues."
        ),
        "screen_width": 1440,
        "screen_height": 900,
    },
    "ai_agent": {
        "prompt": (
            "You are a computer use agent (an AI that navigates websites programmatically). "
            "Your goal is to complete tasks on this site by identifying and interacting with UI elements. "
            "Evaluate:\n"
            "- Are interactive elements unambiguous? Can you confidently identify which button to click?\n"
            "- Are there competing CTAs where you'd be uncertain which is the primary action?\n"
            "- Is the page structure predictable — do similar pages follow similar patterns?\n"
            "- Are element labels descriptive enough to determine their function without visual context?\n"
            "- Would you need to guess or use heuristics to navigate, or is intent clear from the markup?\n"
            "- Are there any patterns that would cause a navigation loop or dead end?\n"
            "Try to complete the site's primary user flow (learn about product → view pricing → sign up). "
            "Note every point where a computer use agent would make a wrong choice or get stuck."
        ),
        "screen_width": 1440,
        "screen_height": 900,
    },
}


async def _evaluate_as_segment(
    url: str,
    segment: str,
    *,
    output_dir: str,
) -> SegmentEvaluation:
    config = SEGMENT_CONFIGS[segment]

    security = _security_options_for(url)
    nova_kwargs = {
        "starting_page": url,
        "headless": True,
        "screen_width": config["screen_width"],
        "screen_height": config["screen_height"],
    }
    if security:
        nova_kwargs["security_options"] = security

    async with AsyncNovaAct(**nova_kwargs) as nova:
        # Navigate and interact from this segment's perspective
        await nova.act(
            f"Navigate this website from the perspective described below. "
            f"Explore the site, click links, try interactive elements.\n\n{config['prompt']}"
        )

        # Extract structured evaluation
        result = await nova.act_get(
            f"Based on your navigation of this site as described below, provide your evaluation.\n\n"
            f"{config['prompt']}",
            schema=SegmentEvaluation.model_json_schema(),
        )
        evaluation = SegmentEvaluation.model_validate(result.parsed_response)

    evaluation.segment_name = segment
    evaluation.url = url
    return evaluation


async def run_segment_inspection(
    url: str,
    *,
    segment: str = "new_user",
    output_dir: str = "/tmp/design-inspector",
) -> SegmentEvaluation:
    os.makedirs(output_dir, exist_ok=True)
    return await _evaluate_as_segment(url, segment, output_dir=output_dir)


async def run_parallel_segment_inspections(
    url: str,
    *,
    segments: list[str],
    output_dir: str = "/tmp/design-inspector",
) -> list[SegmentEvaluation]:
    os.makedirs(output_dir, exist_ok=True)

    tasks = [
        _evaluate_as_segment(url, segment, output_dir=output_dir)
        for segment in segments
        if segment in SEGMENT_CONFIGS
    ]

    results = await asyncio.gather(*tasks)
    return list(results)
