---
description: Add a new RSS source to the PM daily digest
argument-hint: "<source name> [RSS URL]"
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash
  - WebFetch
  - WebSearch
  - mcp__n8n-mcp__n8n_get_workflow
  - mcp__n8n-mcp__n8n_update_partial_workflow
---

Add a new RSS source to the productmanager-news-summary project.

The pipeline runs on **n8n** (not GitHub Actions). Workflow: `PM Daily Digest` (ID: `idvoV9PdCjtZPgJw`).

## Input

The user provides: `$ARGUMENTS`

This can be:
- A source name only (e.g., "Shreyas Doshi") — you need to find the RSS feed URL
- A source name + URL (e.g., "Shreyas Doshi https://shreyas.substack.com/feed")

## Steps

1. **Find RSS feed URL** (if not provided)
   - Search the web for the source's blog/newsletter
   - Try common RSS patterns: `/feed`, `/feed.xml`, `/rss`, `/rss.xml`, `/atom.xml`
   - For Substack: `https://<name>.substack.com/feed`
   - Use WebFetch to verify the feed is valid and returns articles

2. **Validate the RSS feed**
   - WebFetch the URL and confirm it returns valid RSS/Atom XML with recent articles
   - If the feed is invalid or unreachable, report to the user and stop

3. **Update n8n workflow — Source Config node**
   - Get current workflow: `n8n_get_workflow` (ID: `idvoV9PdCjtZPgJw`, mode: `full`)
   - Find the `Source Config` Code node's `jsCode`
   - Add `["來源名稱", "https://example.com/feed"]` to the `sources` array
   - Use `n8n_update_partial_workflow` with `updateNode` operation to update the node

4. **Update n8n workflow — Build LINE Message node**
   - Find the `Build LINE Message` Code node's `jsCode`
   - Add the source name to the `sourceOrder` array (controls display order in LINE message)
   - Use `n8n_update_partial_workflow` to update the node

5. **Update local files** (keep in sync)
   - Edit `fetch_articles.py`: add the new entry to `RSS_FEEDS` dict
   - Edit `CLAUDE.md`: add a row to the source table with name and a brief note

6. **Deactivate → Reactivate workflow**
   - Required after node updates for changes to take effect

7. **Report results**
   - Show the user: source name, RSS URL, number of articles found
   - Ask the user if they want to commit + push

8. **Commit + push** (only if user confirms)
   - `git add fetch_articles.py CLAUDE.md`
   - Commit with message: `Add <source name> RSS source`
   - Push to origin

9. **Update memory**
   - Update `/Users/william/.claude/projects/-Users-william/memory/pm-news-summary.md` RSS Sources section

## Important Notes

- n8n (Zeabur) IP 不會被 Substack 擋，Substack 來源可以直接加。
- Do NOT add sources that require JavaScript rendering (e.g., Reforge Blog on Framer).
- After updating n8n nodes, always deactivate → reactivate the workflow.
