from __future__ import annotations

import asyncio

from orillia.nova import nova_session
from orillia.schemas import SegmentEvaluation


SEGMENT_PROMPTS: dict[str, str] = {
    "new_user": (
        "You are a first-time visitor who has never heard of this product. You landed here "
        "from a Google search. Navigate the site and evaluate:\n"
        "- Is it immediately clear what this product does and who it's for?\n"
        "- Can you figure out how to get started without any prior knowledge?\n"
        "- Is the onboarding path obvious -- do you know what steps to take?\n"
        "- Are there any moments where you feel lost, confused, or unsure what to do next?\n"
        "- How much jargon or assumed knowledge is there?\n"
        "Try to sign up or start using the product. Note every point where you hesitate."
    ),
    "power_user": (
        "You are an experienced user who has used this product daily for months. You know "
        "exactly what you want to do and you want to do it fast. Navigate the site and evaluate:\n"
        "- Can you quickly find the feature or setting you need?\n"
        "- Are there keyboard shortcuts, search, or quick-access patterns?\n"
        "- Is information density appropriate -- enough detail without clutter?\n"
        "- Are there unnecessary steps or confirmations that slow you down?\n"
        "- Can you accomplish your goal in the minimum number of clicks?\n"
        "Try to navigate to settings, find a specific project, and check billing."
    ),
    "casual_user": (
        "You are a casual, infrequent user checking in on mobile. You have limited "
        "attention and might be multitasking. Navigate the site and evaluate:\n"
        "- Are touch targets large enough to tap accurately on a phone?\n"
        "- Is the most important information visible without excessive scrolling?\n"
        "- Can you accomplish your main task quickly before getting distracted?\n"
        "- Does the site have a responsive layout that works on small screens?\n"
        "- Are there any elements that would not work well on a small screen?\n"
        "Try to check the status of a project and view recent activity."
    ),
    "screen_reader": (
        "You are using a screen reader to navigate this site. Evaluate the semantic structure:\n"
        "- Are headings properly nested (h1 > h2 > h3)?\n"
        "- Do images have alt text? Do icons have accessible labels?\n"
        "- Is the tab order logical -- can you navigate linearly and understand the page?\n"
        "- Are form fields properly labeled?\n"
        "- Are interactive elements (buttons, links) distinguishable from static content?\n"
        "- Are there any content areas that would be invisible or confusing to a screen reader?\n"
        "Navigate through the page as if reading it linearly, noting semantic issues."
    ),
    "ai_agent": (
        "You are a computer use agent (an AI that navigates websites programmatically). "
        "Your goal is to complete tasks on this site by identifying and interacting with UI elements. "
        "Evaluate:\n"
        "- Are interactive elements unambiguous? Can you confidently identify which button to click?\n"
        "- Are there competing CTAs where you'd be uncertain which is the primary action?\n"
        "- Is the page structure predictable -- do similar pages follow similar patterns?\n"
        "- Are element labels descriptive enough to determine their function without visual context?\n"
        "- Would you need to guess or use heuristics to navigate, or is intent clear from the markup?\n"
        "- Are there any patterns that would cause a navigation loop or dead end?\n"
        "Try to complete the site's primary user flow (learn about product, view pricing, sign up). "
        "Note every point where a computer use agent would make a wrong choice or get stuck."
    ),
}


async def run_segment_inspection(url: str, *, segment: str = "new_user") -> SegmentEvaluation:
    prompt = SEGMENT_PROMPTS[segment]

    async with nova_session(url) as nova:
        await nova.act(
            f"Navigate this website from the perspective described below. "
            f"Explore the site, click links, try interactive elements.\n\n{prompt}"
        )

        result = await nova.act_get(
            f"Based on your navigation of this site as described below, provide your evaluation.\n\n"
            f"{prompt}",
            schema=SegmentEvaluation.model_json_schema(),
        )
        evaluation = SegmentEvaluation.model_validate(result.parsed_response)

    evaluation.segment_name = segment
    evaluation.url = url
    return evaluation


async def run_parallel_segment_inspections(
    url: str,
    *,
    segments: list[str],
) -> list[SegmentEvaluation]:
    tasks = [
        run_segment_inspection(url, segment=segment)
        for segment in segments
        if segment in SEGMENT_PROMPTS
    ]
    return list(await asyncio.gather(*tasks))
