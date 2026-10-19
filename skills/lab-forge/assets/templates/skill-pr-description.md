---
name: pr-description
description: Writes a short PR/MR description from the diff and the task: what and why, how it was checked, known gaps. Use when the user prepares a pull or merge request or says "describe the PR", "write MR text".
---

# pr-description

Use the repo's template if it exists ({{pr_template_path}}); otherwise:

**What and why** - one paragraph, plain words.
**Steps** - numbered, one line each, in the order a reviewer should read.
**Checked by** - commands run, tests added, metric `baseline -> new` for DS work.
**Gaps** - known limitations, follow-up tickets.
{{ticket_link_line}}

Rules: no marketing words, no emoji, no mention of AI. Under 25 lines unless the
change is large. Language: {{lang_docs}}.
