
from __future__ import annotations
import os, re, time, requests, feedparser
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dtp, tz

ROOT = os.path.dirname(os.path.dirname(__file__)) 
BASE = ROOT
OUTDIR = os.path.join(ROOT, "data", "raw", "events")
os.makedirs(OUTDIR, exist_ok=True)
TZ_ET = tz.gettz("America/New_York")

INDEX_URL = "https://www.federalreserve.gov/feeds/feeds.htm"

def discover_feeds():
    r = requests.get(INDEX_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").strip().lower()
        href = a["href"]
        if "monetary policy" in text and "press" in text:
            out["press_monetary"] = requests.compat.urljoin(INDEX_URL, href)
        if text == "all speeches" or ("speeches" in text and "all" in text):
            out["speeches"] = requests.compat.urljoin(INDEX_URL, href)
    out.setdefault("press_monetary", "https://www.federalreserve.gov/feeds/press_monetary.xml")
    out.setdefault("speeches", "https://www.federalreserve.gov/feeds/speeches.xml")
    return out

def parse_rss(url):
    d = feedparser.parse(url)
    items = []
    for e in d.entries:
        title = e.get("title","").strip()
        link = e.get("link")
        pub = e.get("published") or e.get("updated") or e.get("pubDate")
        try:
            dt = dtp.parse(pub)
            if dt.tzinfo: dt = dt.astimezone(TZ_ET)
        except Exception:
            dt = None
        items.append({"title": title, "link": link, "event_dt_et": dt})
    return items

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script","style","noscript"]): t.decompose()
    body = soup.find("div", {"id":"article"}) or soup
    text = body.get_text("\n")
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text

def main():
    import yaml
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml"), "r", encoding="utf-8"))
    start_dt = dtp.parse(cfg.get("start_date","2020-10-01")).astimezone(TZ_ET)
    feeds = discover_feeds()

    rows = []
    for tag, url in feeds.items():
        items = parse_rss(url)
        items = [it for it in items if it["event_dt_et"] and it["event_dt_et"] >= start_dt]
        for it in items:
            try:
                r = requests.get(it["link"], timeout=30)
                r.raise_for_status()
                text = extract_text(r.text)
                rows.append({
                    "event_id": str(abs(hash(str(it["event_dt_et"])+it["title"])) % 10**12),
                    "doc_id": str(abs(hash(it["link"])) % 10**12),
                    "event_dt_et": it["event_dt_et"],
                    "event_type": "PressRelease" if tag=="press_monetary" else "Speech",
                    "title": it["title"],
                    "url": it["link"],
                    "text": text,
                    "word_count": len(text.split())
                })
            except Exception as ex:
                print("WARN:", it["link"], ex)
            time.sleep(0.2)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTDIR, "events_text.csv"), index=False)
    print("Saved events_text.csv:", len(df))

if __name__ == "__main__":
    main()
