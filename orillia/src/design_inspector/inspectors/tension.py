from __future__ import annotations

import os

from nova_act import SecurityOptions
from nova_act.asyncio import NovaAct as AsyncNovaAct

from design_inspector.schemas import TensionReport


def _security_options_for(url: str) -> SecurityOptions | None:
    if url.startswith("file://"):
        path = url.removeprefix("file://")
        directory = os.path.dirname(path)
        return SecurityOptions(allowed_file_open_paths=[f"{directory}/*"])
    return None


TENSION_PROMPT = """\
You are evaluating this web page for design tension points — specific elements or patterns that \
would cause friction for humans browsing this site AND for AI computer use agents trying to \
navigate it programmatically.

For each friction point you find, identify:
1. **Location**: Where exactly on the page is the issue (section, element)?
2. **Description**: What is the concrete problem?
3. **Who it affects**: Does this confuse humans, AI agents, or both? Explain why for each.
4. **Severity**: Is it critical (blocks progress), warning (causes confusion), or info (suboptimal)?
5. **What should change**: Give a specific, actionable design instruction (not code — design intent).
6. **Why it matters**: What goes wrong if this isn't addressed?

Look for these categories of issues:
- **Ambiguous CTAs**: Buttons/links where the user can't predict what will happen
- **Dead ends**: Elements that look interactive but go nowhere
- **Inconsistent patterns**: Elements that behave differently than similar elements elsewhere
- **Missing affordances**: Interactive elements that don't look clickable, or static elements that look clickable
- **Unclear hierarchy**: When it's not obvious what the primary action or most important content is
- **Broken mental models**: When the page contradicts expectations set by other pages on the site
- **Machine-hostile patterns**: Elements an AI agent would struggle to identify, classify, or interact with
- **Misleading indicators**: Colors, icons, or labels that suggest the wrong meaning

Also identify any recurring anti-patterns across the page.

Be thorough but concrete. Every finding should be specific enough that a designer could act on it immediately."""


INTERACTION_TEST_PROMPT = """\
Now test the interactive elements on this page. Try clicking buttons, links, and any elements \
that appear interactive. For each one, note whether it behaved as expected. Focus on elements \
that look like they should do something but don't, or elements that do something unexpected.

Important: Stay on this page. If a click navigates you away, note that and come back."""


async def run_tension_inspection(
    url: str,
    *,
    output_dir: str = "/tmp/design-inspector",
) -> TensionReport:
    os.makedirs(output_dir, exist_ok=True)

    security = _security_options_for(url)
    nova_kwargs: dict = {"starting_page": url, "headless": True}
    if security:
        nova_kwargs["security_options"] = security

    async with AsyncNovaAct(**nova_kwargs) as nova:
        # Scroll through the full page so Nova Act sees everything
        await nova.act("Scroll slowly through the entire page from top to bottom, observing all content and elements")

        # Test interactive elements to discover broken/misleading ones
        await nova.act(INTERACTION_TEST_PROMPT)

        # Extract the structured tension report
        result = await nova.act_get(
            TENSION_PROMPT,
            schema=TensionReport.model_json_schema(),
        )
        report = TensionReport.model_validate(result.parsed_response)

    report.url = url
    return report
