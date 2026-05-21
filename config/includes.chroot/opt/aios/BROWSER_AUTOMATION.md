# Browser Automation Guide

The AIOS autonomous planner now supports browser automation tasks. This allows AI agents to autonomously navigate websites, take screenshots, extract information, and perform web interactions.

## How It Works

1. **Browser Integration**: The `AIBrowser` class (Playwright-based) is initialized in the main AIOS bootstrap
2. **Task Planner Support**: The `TaskPlanner` generates steps that include browser actions
3. **Task Executor**: The `TaskAutomationEngine` executes browser steps in autonomous goal loops
4. **Step Types**: Browser actions are defined as steps with `type: "browser"` and an `action` dict

## Supported Browser Actions

The following actions can be used in autonomous plans:

### Navigation & Inspection
- `navigate` - Navigate to a URL
- `screenshot` - Capture page screenshot
- `get_text` - Extract page text
- `get_links` - Extract all links
- `get_elements` - Find interactive elements
- `dom_snapshot` - Get full HTML

### Interaction
- `click` - Click element by selector or text
- `type` - Type text into input field
- `press` - Press keyboard key
- `execute_js` - Execute JavaScript

## Example: Autonomous Goal with Browser

Add to `agent-config.yaml`:

```yaml
autonomy:
  goal_tasks:
    - id: web-research-goal
      goal: "Visit example.com and take a screenshot of the homepage"
      cwd: .
      retry_limit: 1
```

## Example: Task with Browser Steps

```python
task = {
    "id": "web-task",
    "description": "Navigate and analyze a webpage",
    "steps": [
        {
            "type": "browser",
            "action": {
                "action": "navigate",
                "url": "https://example.com"
            }
        },
        {
            "type": "browser",
            "action": {
                "action": "screenshot",
                "label": "homepage"
            }
        },
        {
            "type": "model",
            "model": "gpt-4o-mini",
            "prompt": "Describe what you see in this screenshot"
        }
    ]
}
```

## Configuration

Browser settings via environment variables:

```bash
# Headless mode (default: true)
export KOII_BROWSER_HEADLESS=true

# Screenshot directory (default: ./data/screenshots)
export KOII_BROWSER_SCREENSHOT_DIR=./data/screenshots
```

## Usage Examples

### Example 1: Simple Screenshot
```python
goal = "Take a screenshot of github.com"
# The planner will generate:
# {
#   "steps": [
#     {"type": "browser", "action": {"action": "navigate", "url": "https://github.com"}},
#     {"type": "browser", "action": {"action": "screenshot", "label": "github"}}
#   ]
# }
```

### Example 2: Search and Extract
```python
goal = "Search for 'AI agents' on Google and list the top 5 results"
# The planner generates steps to:
# 1. Navigate to google.com
# 2. Click search box
# 3. Type query
# 4. Take screenshot
# 5. Extract links using get_links
```

### Example 3: Form Submission
```python
goal = "Submit a contact form with name 'AIOS' and email 'aios@example.com'"
# Steps:
# 1. Navigate to form URL
# 2. Type name into #name field
# 3. Type email into #email field
# 4. Click submit button
# 5. Screenshot to verify success
```

## Running the Demo

```bash
# Test browser automation separately
python scripts/demo_browser_automation.py

# Run full AIOS with browser-enabled autonomy
python -m src.main

# Check generated screenshots
ls data/screenshots/
```

## Troubleshooting

### Browser not starting
- Ensure Playwright is installed: `pip install playwright`
- Install chromium: `playwright install chromium`

### Screenshots not saved
- Check `./data/screenshots` directory exists or is writable
- Set `KOII_BROWSER_SCREENSHOT_DIR` to a valid path

### Actions fail due to timeouts
- Increase Playwright timeout (default: 10s)
- Check internet connectivity for `navigate` actions
- Verify selectors/text exist on page

## Architecture

```
┌─────────────────────────────────────────┐
│  Autonomous Goal Loop                   │
│  (AutonomousTaskLoop)                   │
└──────────────────┬──────────────────────┘
                   │
                   v
          ┌────────────────┐
          │  Task Planner  │
          │ (generates steps)
          └────────┬───────┘
                   │
                   v
    ┌──────────────────────────────┐
    │  Task Automation Engine      │
    │ - Executes shell steps       │
    │ - Executes model steps       │
    │ - Executes browser steps ←───┼─── NEW!
    │ - Executes file ops          │
    └──────────────┬───────────────┘
                   │
         ┌─────────┴──────────┐
         v                    v
    ┌─────────┐        ┌──────────┐
    │OSControl│        │ AIBrowser│
    └─────────┘        └──────────┘
```

## Integration Points

- **Planner**: Accepts `browser` step type in task definitions
- **Runner**: Dispatches browser actions to `AIBrowser` instance
- **Event Store**: Records browser interactions in autonomy events
- **Web UI**: Can display screenshots captured during autonomy
