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
if not items:
    print("No episodes found in the feed.")
    exit()

# Namespace map for iTunes elements
ns = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"
}

# CSV columns
fields = [
    "title","link","description","pubDate","releaseDate","guid",
    "episodeType","episode","itunes_title","author","explicit",
    "image","enclosure","duration","subtitle","summary","clean"
]

# Build row for latest episode only
item = items[0]  # latest episode
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

# Read existing CSV, prepend new row
try:
    with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
except FileNotFoundError:
    reader = []

with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerow(row)  # new latest episode first
    for existing_row in reader:
        writer.writerow(existing_row)

print(f"Prepended latest episode: {row['title']}")
