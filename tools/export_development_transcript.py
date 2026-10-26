"""Export visible project messages from explicitly supplied local session logs."""

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


AUTOMATIC_TAGS = (
    "in-app-browser-context", "environment_context", "recommended_plugins",
    "external_codex_apps_open_page", "external_codex_apps_writing_block_edits",
    "turn_aborted",
)


def redact(text, counts):
    """Purpose: remove personal paths/emails and recognizable secrets. Inputs: text and redaction counter. Returns: shareable text."""
    patterns = (
        (r"(?i)(?<=password )(?=[A-Za-z0-9!@#$%^&*?.+-]*[0-9])[A-Za-z0-9!@#$%^&*?.+-]{8,}", "[redacted account password]", "account_passwords"),
        (r"(?i)C:[/\\]Users[/\\][^/\\\s\"<>]+", "[user home]", "home_paths"),
        (r"\b(?:ghp_|github_pat_|sk-|hf_)[A-Za-z0-9_-]{20,}\b", "[redacted token]", "tokens"),
        (r"https://[^\s/@]+:[^\s/@]+@", "https://[redacted credentials]@", "url_credentials"),
    )
    for pattern, replacement, label in patterns:
        text, number = re.subn(pattern, replacement, text)
        counts[label] += number
    for email in set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)):
        if not email.lower().endswith((".test", ".invalid", "@example.com", "@example.org")):
            counts["personal_emails"] += text.count(email)
            text = text.replace(email, "[redacted email]")
    return text


def visible_text(message, counts):
    """Purpose: extract displayable text and label attachment omissions. Inputs: message record and counters. Returns: cleaned text."""
    parts = message.get("content", [])
    text = "\n".join(part.get("text", "") for part in parts if part.get("type") in ("input_text", "output_text"))
    for tag in AUTOMATIC_TAGS:
        text = re.sub(fr"<{tag}\b[^>]*>.*?</{tag}>", "", text, flags=re.S)
    text = re.sub(r"<image\b[^>]*>.*?</image>", "[Image attachment omitted; see the surrounding discussion.]", text, flags=re.S)
    text = re.sub(r"<image\b[^>]*/>", "[Image attachment omitted.]", text)
    if any(part.get("type") in ("input_image", "image") for part in parts):
        text += "\n\n[Image attachment omitted.]"
    if "## My request:" in text:
        text = text.split("## My request:", 1)[1]
    if text.strip().startswith("<send_user_message_question_reply>"):
        raw = re.sub(r"</?send_user_message_question_reply>", "", text).strip()
        answers = json.loads(raw)
        text = "\n\n".join("Question shown: " + answer["question"] + "\n\nStudent answer: " + answer["answer"] for answer in answers)
    if text.strip().startswith("# Files pasted by the user:"):
        # Retain the paste title and the student's text, without inventing missing attachment contents.
        text += "\n\n[The referenced pasted-file contents are not reproduced in this message export.]"
    return redact(text.strip(), counts)


def read_messages(sources, start, end):
    """Purpose: collect visible messages from approved source types and time range. Inputs: explicit paths/ISO bounds. Returns: messages, source metadata, counters."""
    messages, metadata, seen = [], [], set()
    counts = Counter()
    for path in sources:
        raw = path.read_bytes()
        entries = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        meta = entries[0].get("payload", {})
        if entries[0].get("type") != "session_meta" or meta.get("source") not in ("vscode", "cli"):
            raise ValueError("Only primary user-facing IDE/CLI sessions may be exported: " + path.name)
        included = 0
        for entry in entries:
            stamp = entry.get("timestamp", "")
            item = entry.get("payload", {})
            if not start <= stamp < end or entry.get("type") != "response_item" or item.get("type") != "message":
                continue
            role = item.get("role")
            if role not in ("user", "assistant"):
                continue
            if role == "assistant" and (item.get("channel") not in (None, "commentary", "final") or item.get("phase") not in (None, "commentary", "final", "final_answer")):
                continue
            key = item.get("id") or (stamp, json.dumps(item.get("content"), sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            text = visible_text(item, counts)
            if not text:
                continue
            messages.append({"timestamp": stamp, "role": role, "phase": item.get("phase") or item.get("channel") or "message", "text": text})
            included += 1
        metadata.append({"filename": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "included_messages": included})
    messages.sort(key=message_timestamp)
    return messages, metadata, dict(counts)


def message_timestamp(message):
    """Purpose: order source messages without inferring missing turns. Inputs: exported message. Returns: recorded ISO timestamp."""
    return message["timestamp"]


def main():
    """Purpose: create a reproducible visible-message attachment. Inputs: CLI source paths, bounds, destination. Returns: None; writes Markdown and JSON manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    messages, sources, redactions = read_messages(args.source, args.start, args.end)
    if not messages:
        raise ValueError("No visible project messages in the specified interval")
    headings = [
        "# SmartBrew Lab 3 - available development conversation",
        "Exported 26 October 2026 from three local primary project-chat session segments. Source timestamps below are UTC, as recorded in the logs. The development interval covers 20-22 October 2026 (Europe/Berlin), from the Lab 3 request through the repository reorganization report.",
        "## Scope and provenance",
        "This attachment preserves the available student prompts and visible Codex commentary/final replies in chronological order. It is an actual message export, not a reconstructed dialogue. The short reading guide remains in AI_CONVERSATION.md; the original assignment prompt is also in MAIN_PROMPT.md. Message counts and source-file SHA-256 hashes are in DEVELOPMENT_TRANSCRIPT_MANIFEST.json.",
        "System/developer instructions, private reasoning, tool calls/results, approval-review sessions and automatically supplied browser/environment context are excluded. UI question replies are displayed as their question and student answer. Image bytes and separately pasted-file contents are not bundled. The reported non-public account password, personal email addresses, home-directory prefixes and recognizable token formats are redacted; public demo credentials remain. Apart from these declared transformations, message wording is preserved, including historical errors and unverified claims. Later tests and corrections supersede earlier assurances.",
        "This is the available Codex-side conversation. Gemini text relayed by the student is a quoted proposal, not direct evidence of Gemini execution. The original separate Gemini/Antigravity session transcript is unavailable in these sources; its contribution is summarized in AI_CONVERSATION.md and supported by committed files and test records. Code written through tools is retained in the repository and Git history, rather than represented as an assistant prose reply.",
        "## Current authorship clarification - 26 October 2026",
        "The student clarified that earlier limited AI assistance with Assignment 2 was not comparable to Lab 3's extensive generation. Historical assistant statements inferring that Assignment 2 was AI-authored or could not serve as the human-elicited comparison baseline were unsupported and are withdrawn. The comparison uses the group's actual preserved submission; later generated review corrections are separate materials. Original messages below remain unchanged as historical evidence, including superseded assertions. See the current clarification in AI_CONVERSATION.md and LAB3_REPORT.md.",
        "## Recorded messages",
    ]
    for number, message in enumerate(messages, 1):
        label = "Student" if message["role"] == "user" else "Codex"
        stamp = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S UTC")
        headings.append(f"### {number:03d} - {label} - {stamp} ({message['phase']})")
        # Quote every line so headings/code in the original message cannot change the transcript structure.
        headings.append("\n".join("> " + line if line else ">" for line in message["text"].splitlines()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(headings) + "\n", encoding="utf-8", newline="\n")
    manifest = {"export_date": "2026-10-26", "start_inclusive_utc": args.start, "end_exclusive_utc": args.end, "messages": len(messages), "roles": dict(Counter(message["role"] for message in messages)), "sources": sources, "redactions": redactions, "transcript_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "scope": "Available visible Codex-side development messages; declared omissions and redactions are explained in the transcript."}
    args.output.with_name("DEVELOPMENT_TRANSCRIPT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"messages": len(messages), "roles": manifest["roles"], "redactions": redactions, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
