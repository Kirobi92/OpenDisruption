#!/usr/bin/env python3
"""
Nutzi eNVenta Help Converter
Konvertiert alle HTML-Hilfeseiten zu sauberem Markdown.
Output: services/nutzi/data/chapters/*.md + data/index.json
"""

import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


HTML_DIR = Path("/tmp/enventa-help/OnlineHilfe_eNVenta4.5_de/files/html")
JSON_DIR = Path("/tmp/enventa-help/OnlineHilfe_eNVenta4.5_de/files/json")
OUT_DIR = Path(__file__).parent.parent / "data"


class ContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_tags = {"script", "style", "nav", "head"}
        self.heading_tags = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### "}
        self.current_skip = None
        self.current_tag = None
        self.in_table = False
        self.table_row = []
        self.table_rows = []
        self.table_header_done = False

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip = tag
        self.current_tag = tag
        if tag == "table":
            self.in_table = True
            self.table_rows = []
            self.table_header_done = False
        elif tag == "tr":
            self.table_row = []
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("- ")
        elif tag in self.heading_tags:
            self.parts.append("\n" + self.heading_tags[tag])

    def handle_endtag(self, tag):
        if tag == self.current_skip:
            self.current_skip = None
        if tag in {"h1", "h2", "h3", "h4", "p", "div"}:
            self.parts.append("\n")
        elif tag == "tr" and self.in_table:
            self.table_rows.append(self.table_row[:])
            self.table_row = []
        elif tag == "table":
            self.in_table = False
            if self.table_rows:
                # Build markdown table
                col_count = max(len(r) for r in self.table_rows) if self.table_rows else 0
                if col_count > 0:
                    header = self.table_rows[0] + [""] * (col_count - len(self.table_rows[0]))
                    self.parts.append("\n| " + " | ".join(header) + " |\n")
                    self.parts.append("| " + " | ".join(["---"] * col_count) + " |\n")
                    for row in self.table_rows[1:]:
                        row = row + [""] * (col_count - len(row))
                        self.parts.append("| " + " | ".join(row) + " |\n")
                    self.parts.append("\n")
            self.table_rows = []

    def handle_data(self, data):
        if self.current_skip:
            return
        d = data.strip()
        if not d:
            return
        if self.in_table and self.current_tag in {"td", "th"}:
            self.table_row.append(d)
        else:
            self.parts.append(d + " ")

    def get_text(self):
        text = "".join(self.parts)
        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()


def convert_html_to_markdown(chapter_id: str) -> str:
    path = HTML_DIR / f"{chapter_id}.html"
    if not path.exists():
        return ""
    extractor = ContentExtractor()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            extractor.feed(f.read())
    except Exception:
        return ""
    return extractor.get_text()


def build_topic_map(index_data: list) -> dict:
    """Build chapter_id → [topic labels] mapping."""
    chap_to_topics: dict[str, list[str]] = {}

    def recurse(items, prefix=""):
        for item in items:
            label = item.get("label", "")
            for chap in item.get("chapters", []):
                chap_to_topics.setdefault(chap, []).append(label)
            recurse(item.get("children", []), label)

    recurse(index_data)
    return chap_to_topics


def main():
    print("Nutzi eNVenta Help Converter")
    print(f"HTML source: {HTML_DIR}")
    print(f"Output dir:  {OUT_DIR}")

    chapters_dir = OUT_DIR / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    # Load index
    with open(JSON_DIR / "index.json", encoding="utf-8") as f:
        index_data = json.load(f)
    chap_to_topics = build_topic_map(index_data)

    # Find all HTML files
    html_files = sorted(HTML_DIR.glob("*.html"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
    print(f"Converting {len(html_files)} HTML files...")

    summary = []
    skipped = 0

    for i, html_file in enumerate(html_files):
        chap_id = html_file.stem
        md_text = convert_html_to_markdown(chap_id)

        if not md_text or len(md_text) < 30:
            skipped += 1
            continue

        topics = chap_to_topics.get(chap_id, [])
        topic_str = topics[0] if topics else f"Kapitel {chap_id}"

        # Write markdown file
        md_path = chapters_dir / f"{chap_id}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"---\nchapter_id: \"{chap_id}\"\ntopics: {json.dumps(topics, ensure_ascii=False)}\nsource: eNVenta 4.5 Onlinehilfe\n---\n\n")
            f.write(f"# {topic_str}\n\n")
            f.write(md_text)

        summary.append({
            "chapter_id": chap_id,
            "title": topic_str,
            "topics": topics,
            "char_count": len(md_text),
        })

        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(html_files)} converted...")

    # Write master index
    master_index = {
        "total_chapters": len(summary),
        "skipped": skipped,
        "topics_count": len(index_data),
        "chapters": summary,
    }
    with open(OUT_DIR / "master_index.json", "w", encoding="utf-8") as f:
        json.dump(master_index, f, ensure_ascii=False, indent=2)

    # Write topic→chapters lookup
    topic_lookup = {}
    for item in index_data:
        topic_lookup[item["label"]] = {
            "chapters": item.get("chapters", []),
            "children": [c["label"] for c in item.get("children", [])],
        }
    with open(OUT_DIR / "topic_lookup.json", "w", encoding="utf-8") as f:
        json.dump(topic_lookup, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Converted: {len(summary)}, Skipped: {skipped}")
    print(f"Master index: {OUT_DIR / 'master_index.json'}")


if __name__ == "__main__":
    main()
