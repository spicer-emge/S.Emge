
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from html import escape
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent


class PostParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.metadata = {}
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "title":
            self.in_title = True

        if tag == "meta":
            if "name" in attrs:
                self.metadata[attrs["name"]] = attrs.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


posts = []

for file in (ROOT / "posts").glob("*.html"):
    parser = PostParser()
    parser.feed(file.read_text(encoding="utf-8"))

    if "date" not in parser.metadata:
        continue

    date = datetime.fromisoformat(parser.metadata["date"])

    posts.append({
        "title": parser.title.strip(),
        "date": date,
        "timezone": parser.metadata.get("timezone", ""),
        "preview": parser.metadata.get("preview", ""),
        "url": quote(f"posts/{file.name}")
    })

posts.sort(key=lambda post: post["date"].timestamp(), reverse=True)

entries = []

for post in posts:
    date = post["date"]
    timestamp = date.strftime("%Y.%m.%d — %H:%M:%S")
    timestamp += " " + post["timezone"]

    image = ""

if post["preview"]:
    preview = post["preview"]

    if not (ROOT / preview).is_file():
        raise FileNotFoundError(f"Preview image not found: {preview}")

    image = f'<img src="{escape(preview)}" alt="">'
    entries.append(f"""
        <div class="post">
            <a href="{post['url']}" class="preview">
                {escape(post['title'])}
                {image}
            </a>
            <time datetime="{date.isoformat()}">
                {escape(timestamp.strip())}
            </time>
        </div>
    """)

index = ROOT / "index.html"
html = index.read_text(encoding="utf-8")

start = "<!-- POSTS START -->"
end = "<!-- POSTS END -->"

before = html.split(start, 1)[0]
after = html.split(end, 1)[1]

html = before + start + "\n".join(entries) + end + after

index.write_text(html, encoding="utf-8")

print(f"Homepage updated with {len(posts)} posts.")
