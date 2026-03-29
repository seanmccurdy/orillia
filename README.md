# Orillia

An MCP server that uses [Amazon Nova Act](https://github.com/aws/nova-act) to evaluate web design and UX quality from the perspective of both human users and computer use agents.

## Thesis

The AI boom is flooding the web with sites built without design rigor. These sites frustrate humans **and** computer use agents alike — unclear CTAs, broken flows, inconsistent patterns. A computer use agent is uniquely positioned to evaluate this because it actually *navigates* like a user — it experiences the flow, not just screenshots it.

Improving design standards for humans simultaneously makes computer use agents more effective, creating a virtuous cycle.

**This tool evaluates and critiques only — it never fixes.** It returns detailed findings and actionable instructions. The calling agent decides what to do.

## Install

```bash
git clone https://github.com/yourusername/orillia.git
cd orillia/mcp
uv sync
```

You will need a [Nova Act API key](https://github.com/aws/nova-act) to run evaluations.

## Setup by Client

In all examples below, replace `/path/to/orillia` with the absolute path to where you cloned this repo, and `your-key-here` with your Nova Act API key.

### Claude Code

```bash
claude mcp add orillia \
  -e NOVA_ACT_API_KEY=your-key-here \
  -- uv run --quiet --directory /path/to/orillia/mcp orillia
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "orillia": {
      "command": "uv",
      "args": ["run", "--quiet", "--directory", "/path/to/orillia/mcp", "orillia"],
      "env": {
        "NOVA_ACT_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "orillia": {
      "command": "uv",
      "args": ["run", "--quiet", "--directory", "/path/to/orillia/mcp", "orillia"],
      "env": {
        "NOVA_ACT_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "orillia": {
      "command": "uv",
      "args": ["run", "--quiet", "--directory", "/path/to/orillia/mcp", "orillia"],
      "env": {
        "NOVA_ACT_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Kiro

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "orillia": {
      "command": "uv",
      "args": ["run", "--quiet", "--directory", "/path/to/orillia/mcp", "orillia"],
      "env": {
        "NOVA_ACT_API_KEY": "your-key-here"
      }
    }
  }
}
```

### ChatGPT

ChatGPT does not support MCP servers.

### Run Standalone

```bash
export NOVA_ACT_API_KEY=your-key-here
cd mcp
uv run --quiet orillia
```

## Tools

| Tool | What It Does |
|------|-------------|
| `evaluate_flow` | Navigate a site, follow links, evaluate page-to-page coherence and information architecture |
| `find_tension_points` | Identify friction points where humans or AI agents would get confused, stuck, or lost |
| `evaluate_as_segment` | Evaluate from a specific user perspective: `new_user`, `power_user`, `casual_user`, `screen_reader`, `ai_agent` |
| `full_evaluation` | Run all three analyses. Recommended starting point. |
| `export_training_data` | Full evaluation + export findings as JSONL for training computer use agent models |

## Demo

The package includes a deliberately flawed 4-page demo site (`mcp/src/orillia/demo/flawed_site/`) with holistic UX problems:

- **index.html**: Competing CTAs, vague value prop, terminology inconsistencies
- **pricing.html**: "Most Popular" on the most expensive plan, non-functional toggle, dead-end CTA
- **signup.html**: No plan context, unclear required fields, broken form, promise/delivery mismatch
- **dashboard.html**: No onboarding, different nav structure, misleading metrics, terminology drift

These aren't CSS bugs — they're experiential problems that only a navigating agent would catch.

```
Ask Claude Code: "Evaluate the design of the demo site at file:///path/to/demo/flawed_site/index.html"
```

## Nova Act SDK Features Used

- `NovaAct(starting_page=...)` — browser session management
- `nova.act("natural language")` — navigate, click, scroll, interact
- `nova.act_get(prompt, schema=...)` — structured evaluation extraction via Pydantic
- `nova_act.asyncio.NovaAct` — async sessions for parallel evaluation
- `asyncio.gather()` — concurrent segment evaluations at different viewports
- `screen_width` / `screen_height` — viewport control per user segment
- `nova.page.screenshot()` — evidence capture via Playwright
- `headless=True` — background execution
- Pydantic schema integration — 7 structured models

## Architecture

```
MCP Client (Claude Code, Cursor, etc.)
    │
    ▼
Orillia MCP Server (server.py)
    │
    ├── evaluate_flow ──────► flow.py ──────► Nova Act (navigate pages, evaluate coherence)
    ├── find_tension_points ► tension.py ──► Nova Act (interact with elements, find friction)
    ├── evaluate_as_segment ► segments.py ─► Nova Act (parallel async sessions per segment)
    ├── full_evaluation ────► all three ──► reporting.py (assemble FullReport)
    └── export_training_data ► full_eval ─► reporting.py (JSONL export)
```

## Why This Matters

- **Not visual QA** (Percy/Chromatic): Those pixel-diff against baselines. This evaluates whether the *experience* works.
- **Not accessibility testing** (axe/Lighthouse): Those check WCAG rules. This evaluates holistic UX.
- **Not just for humans**: A site that confuses a human also confuses a computer use agent. Better design = more reliable agents.
- **Computer use as evaluator**: Nova Act doesn't just screenshot — it navigates, clicks, fills forms. It finds problems static analysis never could.
