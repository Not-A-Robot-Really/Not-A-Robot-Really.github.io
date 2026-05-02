#!/usr/bin/env python3
# python .\add_learning_resource_p5_demo.py --title "My Gravity Demo" --code-file .\sketch.js
from __future__ import annotations

import argparse
import shutil
import html
import re
from pathlib import Path


P5_CDN = "https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("title must contain at least one letter or number")
    return slug


def load_code(args: argparse.Namespace) -> str:
    if bool(args.code) == bool(args.code_file):
        raise ValueError("provide exactly one of --code or --code-file")

    if args.code:
        return args.code

    return Path(args.code_file).read_text(encoding="utf-8")


def require_marker(text: str, marker: str, description: str) -> int:
    index = text.find(marker)
    if index < 0:
        raise ValueError(f"could not find {description}")
    return index


def append_inside_block(text: str, pattern: re.Pattern[str], snippet: str, presence_marker: str, description: str) -> str:
    if presence_marker in text:
        return text

    match = pattern.search(text)
    if not match:
        raise ValueError(f"could not find {description}")

    before, body, after = match.groups()
    body = body.rstrip("\n")
    if body:
        body = f"{body}\n{snippet}"
    else:
        body = snippet
    return text[: match.start()] + before + body + after + text[match.end() :]


def insert_before(text: str, marker: str, snippet: str, presence_marker: str, description: str) -> str:
    if presence_marker in text:
        return text

    index = require_marker(text, marker, description)
    return text[:index] + snippet + text[index:]


def insert_after(text: str, marker: str, snippet: str, presence_marker: str, description: str) -> str:
    if presence_marker in text:
        return text

    index = require_marker(text, marker, description) + len(marker)
    return text[:index] + snippet + text[index:]


def replace_once(text: str, old: str, new: str, description: str) -> str:
    if old not in text:
        raise ValueError(f"could not find {description}")
    return text.replace(old, new, 1)


def write_atomic(path: Path, content: str, make_backup: bool) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    backup_path = path.with_suffix(path.suffix + ".bak")

    if make_backup:
        shutil.copy2(path, backup_path)

    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def build_srcdoc(title: str, code: str) -> str:
    safe_code = code.replace("</script>", "<\\/script>")
    doc = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <script src=\"{P5_CDN}\"></script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #f4f6fb;
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    body {{
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    main {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    canvas {{
      display: block;
    }}
  </style>
  <title>{html.escape(title)}</title>
</head>
<body>
  <main id=\"app\"></main>
  <script>
{safe_code}
  </script>
</body>
</html>
"""
    return html.escape(doc, quote=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add a new Learning Resources entry with a dedicated p5.js page.",
    )
    parser.add_argument("--title", required=True, help="Dropdown/page title")
    parser.add_argument("--code", help="Inline p5.js sketch code")
    parser.add_argument("--code-file", help="Path to a file containing p5.js sketch code")
    parser.add_argument(
        "--html",
        default="index.html",
        help="Path to the HTML file to update (default: index.html)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create an .bak backup before writing changes",
    )
    args = parser.parse_args()

    code = load_code(args)
    title = args.title.strip()
    if not title:
        raise ValueError("title cannot be empty")

    slug = slugify(title)
    page_id = f"page-{slug}"
    active_class = f"{slug}-active"

    html_path = Path(args.html)
    text = html_path.read_text(encoding="utf-8")

    if page_id in text or f"showPage('{slug}')" in text:
        raise ValueError(f"an entry for '{slug}' already exists")

    desktop_entry = (
        f"        <li><a href=\"#\" onclick=\"showPage('{slug}'); "
        "var dd=document.getElementById('nav-dropdown-lr'); "
        "dd.classList.remove('open'); dd.classList.add('closed'); return false;\">"
        f"{html.escape(title)}</a></li>"
    )
    mobile_entry = (
        f"    <a class=\"hamburger-nav-item hamburger-sub-item\" href=\"#\" onclick=\"showPage('{slug}'); closeHamburger(); return false;\">\n"
        "      <svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"#FFFFFF\"><path d=\"M3 5h18v14H3V5zm2 2v10h14V7H5zm2 2h4v4H7V9zm6 0h4v2h-4V9zm0 4h4v2h-4v-2z\"/></svg>\n"
        f"      {html.escape(title)}\n"
        "    </a>"
    )

    srcdoc = build_srcdoc(title, code)
    page_section = (
        f"</div><div id=\"{page_id}\" style=\"min-height:100vh; padding-top:100px; background:#f4f6fb;\">\n"
        "  <div class=\"cw-page-wrap\" style=\"text-align:center;\">\n"
        f"    <h1 class=\"cw-page-title\">{html.escape(title)}</h1>\n"
        "    <p class=\"cw-page-sub\">Interactive p5.js demo.</p>\n"
        f"    <iframe title=\"{html.escape(title, quote=True)}\" srcdoc=\"{srcdoc}\" style=\"width:100%; max-width:960px; height:min(75vh, 720px); border:0; border-radius:16px; background:#fff; box-shadow:0 12px 32px rgba(0,0,0,0.12);\"></iframe>\n"
        "  </div>\n"
    )

    desktop_pattern = re.compile(
        r'(<li class="nav-dropdown" id="nav-dropdown-lr".*?<ul class="dropdown-menu">\n)(.*?)(\n\s*</ul>)',
        re.S,
    )
    mobile_pattern = re.compile(
        r'(<div class="hamburger-sub-menu" id="hamburger-sub-lr"[^>]*>\n)(.*?)(\n\s*</div>)',
        re.S,
    )

    text = append_inside_block(text, desktop_pattern, desktop_entry, f"showPage('{slug}')", "desktop Learning Resources dropdown")
    text = append_inside_block(text, mobile_pattern, mobile_entry, f"closeHamburger(); return false;\">\n      {html.escape(title)}", "mobile Learning Resources submenu")

    text = insert_before(
        text,
        "#page-coolwebsites { display: none; }",
        f"#page-{slug} {{ display: none; }}\n",
        f"#page-{slug} {{ display: none; }}",
        "page switching CSS",
    )
    text = insert_before(
        text,
        "body.team-active",
        f"body.{active_class} #page-main {{ display: none; }}\nbody.{active_class} #page-{slug} {{ display: block; }}\n",
        f"body.{active_class} #page-main",
        "page active CSS",
    )
    text = insert_before(
        text,
        "body.intro-active > #hamburger-overlay,",
        f"body.intro-active > #page-{slug},\n",
        f"body.intro-active > #page-{slug},",
        "intro active selector list",
    )
    text = insert_before(
        text,
        "body.intro-fade-in > #hamburger-overlay,",
        f"body.intro-fade-in > #page-{slug},\n",
        f"body.intro-fade-in > #page-{slug},",
        "intro fade selector list",
    )
    text = replace_once(
        text,
        "</div><div id=\"page-team\">",
        page_section + "</div><div id=\"page-team\">",
        "page insertion anchor",
    )
    text = replace_once(
        text,
        "document.body.classList.remove('demo-active','test-demo-active','team-active','about-active','contact-active','announcements-active','member-active','coolwebsites-active');",
        "document.body.classList.remove('demo-active','test-demo-active','team-active','about-active','contact-active','announcements-active','member-active','coolwebsites-active',"
        f"'{active_class}');",
        "showPage class removal list",
    )
    text = insert_before(
        text,
        "  } else if (page === 'team') {",
        "  } else if (page === '" + slug + "') {\n"
        f"    document.body.classList.add('{active_class}');\n",
        f"page === '{slug}'",
        "showPage branch insertion",
    )

    write_atomic(html_path, text, make_backup=not args.no_backup)
    print(f"Added Learning Resources entry '{title}' as '{slug}' in {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())