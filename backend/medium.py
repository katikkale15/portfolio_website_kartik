from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import feedparser, httpx, os, re
from datetime import datetime

router = APIRouter()

def strip_html(t):
    return re.sub(r"<[^>]+>", "", t or "").strip()

def get_thumb(content):
    m = re.search(r'<img[^>]+src="([^"]+)"', content or "")
    return m.group(1) if m else None

@router.get("")
async def get_posts(limit: int = 5):
    username = os.getenv("MEDIUM_USERNAME", "kartikkale03")
    url = f"https://medium.com/feed/@{username}"
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url)
            r.raise_for_status()
        feed = feedparser.parse(r.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    posts = []
    for entry in feed.entries[:limit]:
        raw = ""
        if hasattr(entry, "content"):  raw = entry.content[0].value
        elif hasattr(entry, "summary"): raw = entry.summary
        pub = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub = datetime(*entry.published_parsed[:6]).strftime("%b %d, %Y")
        posts.append({
            "title":     entry.get("title", ""),
            "url":       entry.get("link",  ""),
            "published": pub,
            "summary":   strip_html(raw)[:220] + "…",
            "thumbnail": get_thumb(raw),
            "tags":      [t.term for t in entry.get("tags", [])][:4],
        })
    return JSONResponse({"posts": posts, "count": len(posts)})
