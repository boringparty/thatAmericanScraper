import requests
import feedparser
import csv
from bs4 import BeautifulSoup

BASE_URL = "https://www.thisamericanlife.org"
RSS_URL = "https://awk.space/tal.xml"

OUTPUT_FILE = "tal_backfill.csv"

# column order you specified
FIELDS = [
    "title","link","description","pubDate","releaseDate","guid","episodeType","episode",
    "itunes_title","author","explicit","image","enclosure","duration","subtitle","summary","clean"
]

def fetch_rss():
    return feedparser.parse(RSS_URL)

def fetch_episode_page(url):
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def parse_episode(entry):
    # basic fields
    title = entry.title
    link = entry.link
    subtitle = entry.get("summary", "").strip()
    pubDate = entry.get("published", "")
    releaseDate = entry.get("tal_releaseDate", "")
    guid = entry.get("guid", "")
    enclosure = entry.enclosures[0].get("href") if entry.enclosures else ""
    episodeType = "Full"
    episode_num, itunes_title = title.split(":", 1)
    episode_num = episode_num.strip()
    itunes_title = itunes_title.strip()
    author = "This American Life"
    explicit = "yes"
    duration = ""  # ignored for now
    summary = ""   # ignored for now
    image = ""
    clean = ""
    description = ""

    # fetch episode page for description, clean file, image
    soup = fetch_episode_page(link)

    # description (subtitle + segments)
    segments = soup.select("div.episode-acts div.tal-episode-act")
    desc_lines = [subtitle] if subtitle else []
    for seg in segments:
        seg_text = seg.get_text("\n", strip=True)
        desc_lines.append(seg_text)
    description = "\n\n".join(desc_lines)

    # image
    img_tag = soup.select_one("figure.tal-episode-image img")
    if img_tag and img_tag.get("src"):
        image = img_tag["src"]

    # clean audio
    clean_link = soup.select_one('a[href*="clean"]')
    if clean_link and clean_link.get("href"):
        clean = clean_link["href"]

    return {
        "title": title,
        "link": link,
        "description": description,
        "pubDate": pubDate,
        "releaseDate": releaseDate,
        "guid": guid,
        "episodeType": episodeType,
        "episode": episode_num,
        "itunes_title": itunes_title,
        "author": author,
        "explicit": explicit,
        "image": image,
        "enclosure": enclosure,
        "duration": duration,
        "subtitle": subtitle,
        "summary": summary,
        "clean": clean,
    }

def main():
    rss = fetch_rss()
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for entry in rss.entries:
            ep_data = parse_episode(entry)
            writer.writerow(ep_data)

if __name__ == "__main__":
    main()
