import csv
import requests
import xml.etree.ElementTree as ET

RSS_URL = "https://www.thisamericanlife.org/podcast/rss.xml"
CSV_FILE = "tal_episodes.csv"

# Fetch RSS
resp = requests.get(RSS_URL)
resp.raise_for_status()

# Parse XML
root = ET.fromstring(resp.content)
items = root.findall(".//item")

# Namespace map
ns = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"
}

# CSV columns
fields = [
    "title","link","description","pubDate","releaseDate","guid",
    "episodeType","episode","itunes_title","author","explicit",
    "image","enclosure","duration","subtitle","summary","clean"
]

with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    
    for item in items:
        row = {
            "title": item.findtext("title", default=""),
            "link": item.findtext("link", default=""),
            "description": item.findtext("itunes:summary", default="", namespaces=ns),
            "pubDate": item.findtext("pubDate", default=""),
            "releaseDate": "",  # empty for now
            "guid": item.findtext("guid", default=""),
            "episodeType": item.findtext("itunes:episodeType", default="", namespaces=ns),
            "episode": item.findtext("itunes:episode", default="", namespaces=ns),
            "itunes_title": item.findtext("itunes:title", default="", namespaces=ns),
            "author": item.findtext("itunes:author", default="", namespaces=ns),
            "explicit": "no" if item.findtext("itunes:explicit", default="", namespaces=ns) == "false" else item.findtext("itunes:explicit", default="", namespaces=ns),
            "image": item.find("itunes:image", ns).attrib.get("href") if item.find("itunes:image", ns) is not None else "",
            "enclosure": item.find("enclosure").attrib.get("url") if item.find("enclosure") is not None else "",
            "duration": item.findtext("itunes:duration", default="", namespaces=ns),
            "subtitle": item.findtext("itunes:subtitle", default="", namespaces=ns),
            "summary": item.findtext("itunes:summary", default="", namespaces=ns),
            "clean": ""
        }
        writer.writerow(row)

print(f"Saved {len(items)} episodes to {CSV_FILE}")
