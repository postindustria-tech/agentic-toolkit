# Upgrade Guide

## Upgrading from pi-dev to dev-practices

If you previously installed the `pi-dev` plugin, follow these steps to upgrade to the renamed `dev-practices` plugin.

### Quick Upgrade (Recommended)

```bash
# 1. Refresh the marketplace to see updated plugin names
/plugin marketplace add postindustria-tech/agentic-toolkit

# 2. Uninstall old plugin
/plugin uninstall pi-dev@agentic-toolkit

# 3. Install new plugin
/plugin install dev-practices@agentic-toolkit
```

That's it! The skills will work exactly the same way.

**Why refresh the marketplace?** Re-adding the marketplace updates its plugin list, so Claude knows `dev-practices` is available and `pi-dev` is no longer offered.

---

## Detailed Upgrade Steps

### Step 1: Refresh the Marketplace

First, update the marketplace to fetch the latest plugin list:

```bash
/plugin marketplace add postindustria-tech/agentic-toolkit
```

This command updates (or re-adds) the marketplace, ensuring Claude knows about the `dev-practices` plugin and that `pi-dev` is no longer available.

**Note:** Re-adding an already-added marketplace updates it - you won't get duplicates.

### Step 2: Check Current Installation

```bash
# List installed plugins
/plugin list
```

Look for `pi-dev@agentic-toolkit` in the output.

### Step 3: Uninstall Old Plugin

```bash
/plugin uninstall pi-dev@agentic-toolkit
```

This removes the old `pi-dev` plugin from your system.

### Step 4: Install New Plugin

```bash
/plugin install dev-practices@agentic-toolkit
```

This installs the renamed `dev-practices` plugin with the same skills.

### Step 5: Verify Installation

```bash
/plugin list
```

You should see `dev-practices@agentic-toolkit` in the list.

---

## For Team Auto-Install (settings.json)

If you have team auto-install configured in `.claude/settings.json`, update the plugin name:

**Old configuration:**
```json
{
  "enabledPlugins": {
    "langgraph-dev@agentic-toolkit": true,
    "pi-dev@agentic-toolkit": true
  }
}
```

**New configuration:**
```json
{
  "enabledPlugins": {
    "langgraph-dev@agentic-toolkit": true,
    "dev-practices@agentic-toolkit": true
  }
}
```

After updating, restart your session for changes to take effect.

---

## What Changed?

### Plugin Name
- **Old:** `pi-dev`
- **New:** `dev-practices`
- **Reason:** Clearer, more generic, not company-specific

### Skill Names
- **Old:** `pi-dev-tdd-workflow`, `pi-dev-session-completion`
- **New:** `dev-practices-tdd-workflow`, `dev-practices-session-completion`

### Functionality
✅ **No changes** - All skills work exactly the same way
✅ **Trigger phrases unchanged** - Skills still auto-load on context
✅ **Content identical** - Same TDD workflow and session completion guides

---

## Skill Invocation Changes

If you directly invoke skills by name, update your commands:

**Old:**
```bash
/pi-dev-tdd-workflow
/pi-dev-session-completion
```

**New:**
```bash
/dev-practices-tdd-workflow
/dev-practices-session-completion
```

**Note:** Most users don't need to change anything - skills auto-load based on context like "use TDD" or "end session".

---

## Troubleshooting

### "Plugin not found" error

If you see an error about `pi-dev` not being found, you've already upgraded or never had it installed. Simply install the new plugin:

```bash
/plugin install dev-practices@agentic-toolkit
```

### Both plugins showing up

If both `pi-dev` and `dev-practices` appear in `/plugin list`, uninstall the old one:

```bash
/plugin uninstall pi-dev@agentic-toolkit
```

### Skills not loading

After upgrading, if skills don't load:

1. Restart your session
2. Verify installation: `/plugin list`
3. Try triggering manually: `/dev-practices-tdd-workflow`

---

## Need Help?

- **Issues:** https://github.com/postindustria-tech/agentic-toolkit/issues
- **Documentation:** See `README.md` and `RELEASE_NOTES.md`

---

## Summary

**Quick version:**
```bash
/plugin uninstall pi-dev@agentic-toolkit
/plugin install dev-practices@agentic-toolkit
```

**For team configs:** Update `settings.json` to use `dev-practices@agentic-toolkit`

**Everything else:** Works the same! 🎉
