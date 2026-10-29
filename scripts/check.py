"""Check documentation, SVG assets, and standard-library CLI examples offline."""

import html
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "__pycache__", "node_modules"}


def main():
    errors = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix == ".svg":
            try:
                ET.parse(path)
            except ET.ParseError as exc:
                errors.append(f"{path.relative_to(ROOT)}: invalid SVG: {exc}")
        if path.suffix != ".md":
            continue
        text = re.sub(r"^(`{3,}|~{3,}).*?^\1[^\n]*$", "", path.read_text(), flags=re.M | re.S)
        links = re.findall(r'!?\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', text)
        links += re.findall(r'(?:href|src)=["\x27]([^"\x27]+)', text)
        for link in links:
            parsed = urlsplit(html.unescape(link))
            if parsed.scheme or parsed.netloc:
                continue
            target = (
                (ROOT if parsed.path.startswith("/") else path.parent) / unquote(parsed.path).lstrip("/")
                if parsed.path
                else path
            )
            if not target.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing target {link}")
                continue
            if parsed.fragment and target.suffix == ".md":
                headings = re.findall(r"^#{1,6}\s+(.+)$", target.read_text(), flags=re.M)
                anchors = {re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings}
                if parsed.fragment not in anchors:
                    errors.append(f"{path.relative_to(ROOT)}: missing heading {link}")
    for sample, expected in [("examples/post.txt", "post 1/1"), ("examples/thread", "post 2/2")]:
        demo = subprocess.run(
            [sys.executable, str(ROOT / "scripts/publish_x.py"), str(ROOT / sample), "--account", "example"],
            capture_output=True,
            text=True,
        )
        if demo.returncode or expected not in demo.stdout or "Dry run: nothing posted" not in demo.stdout:
            errors.append("Real CLI example failed: " + sample + "\n" + demo.stderr)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("OK: documentation links/headings, SVGs, and real standard-library dry-run examples.")


if __name__ == "__main__":
    main()
