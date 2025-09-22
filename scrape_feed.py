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

# CSV columns
fields = [
    "title", "link", "description", "pubDate", "releaseDate", "guid",
    "episodeType", "episode", "itunes_title", "author",
    "explicit", "image", "enclosure", "duration", "subtitle",
    "summary", "clean"
]

with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    
    for item in items:
        def get(tag, ns=None):
            if ns:
                elem = item.find(f"{ns}{tag}")
                return elem.text if elem is not None else ""
            elem = item.find(tag)
            return elem.text if elem is not None else ""
        
        row = {
            "title": get("title"),
            "link": get("link"),
            "description": get("itunes:summary", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "pubDate": get("pubDate"),
            "releaseDate": get("pubDate"),  # placeholder for original air date
            "guid": get("guid"),
            "episodeType": get("itunes:episodeType", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "episode": get("itunes:episode", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "itunes_title": get("itunes:title", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "author": get("itunes:author", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "explicit": "no" if get("itunes:explicit", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}") == "false" else get("itunes:explicit", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "image": get("itunes:image", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "enclosure": item.find("enclosure").attrib.get("url") if item.find("enclosure") is not None else "",
            "duration": get("itunes:duration", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "subtitle": get("itunes:subtitle", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "summary": get("itunes:summary", ns="{http://www.itunes.com/dtds/podcast-1.0.dtd}"),
            "clean": ""
        }
        writer.writerow(row)

print(f"Saved {len(items)} episodes to {CSV_FILE}")
