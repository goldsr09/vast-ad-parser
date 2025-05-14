import requests
from lxml import etree
import time
import sqlite3
import json
from urllib.parse import urlparse, parse_qs

# --- Connect to SQLite database ---
conn = sqlite3.connect("vast_ads.db")
cur = conn.cursor()

# --- Set headers to mimic Roku device ---
headers = {
    "User-Agent": "Roku/DVP-14.5 (14.5.4.5934-46)"
}

# --- Loop 5 times ---
for i in range(5):
    print(f"\n===== Call #{i+1} =====")

    # --- FreeWheel VAST Ad Call URL ---
    url = "https://2ecd5.v.fwmrm.net/ad/g/1?nw=191701&csid=rokufast/atthemovies/roku&caid=0&afid=417275601&pvrn=1745916005113&vprn=1745916005113&flag=+fbad+scpv+emcr+sltp+qtcb+slcb+aeti+vicb+dtrd&metr=1159&prof=191701:trc_ctv_roku_live_prod&resp=vast3&vrdu=180&vdty=variable&vip=68.185.237.137&mode=live&;_fw_vcid2=894bbef2-0a0a-56cf-81a1-43c97d72fbe6&_fw_did=rida:894bbef2-0a0a-56cf-81a1-43c97d72fbe6&_fw_h_user_agent=Roku%2FDVP-14.5%20%2814.5.4.5944-AP%29&_fw_coppa=0&_fw_is_lat=0&_fw_us_privacy=1YNN&platform=rokuplayer&_fw_nielsen_app_id=P2871BBFF-1A28-44AA-AF68-C7DE4B148C32;ptgt=a&tpcl=midroll&slid=4f47aa54-97de-524b-a1b2-9d1bac351049&mind=180&maxd=180&maxa=6"

    # --- Extract channel_name from csid query param ---
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    csid = query_params.get("csid", [""])[0]  # e.g., "rokufast/crimescenes/roku"
    csid_parts = csid.split("/")
    channel_name = csid_parts[1] if len(csid_parts) >= 2 else None

    # --- Fetch the XML ---
    response = requests.get(url, headers=headers)
    print(f"HTTP status: {response.status_code}")

    if response.status_code != 200:
        print("Failed to fetch VAST XML.")
        continue

    xml = response.content
    if not xml.strip():
        print("Empty XML response – skipping")
        continue

    parser = etree.XMLParser(recover=True)
    try:
        tree = etree.fromstring(xml, parser=parser)
    except etree.XMLSyntaxError as e:
        print(f"XML parse error: {e}")
        continue

    # --- Extract Ad data ---
    ads = tree.xpath("//Ad")
    print(f"Found {len(ads)} ads\n")

    for ad in ads:
        ad_id = ad.get("id", "N/A")
        title = ad.xpath(".//AdTitle/text()")
        duration = ad.xpath(".//Duration/text()")
        click_url = ad.xpath(".//ClickThrough/text()")
        creative_id = ad.xpath(".//Creative/@id")
        creative_id = creative_id[0] if creative_id else None

        # --- Collect all media file URLs ---
        media_files = ad.xpath(".//MediaFile")
        media_urls = [mf.text.strip() for mf in media_files if mf.text]

        print(f"Ad ID: {ad_id}")
        print(f"Creative ID: {creative_id if creative_id else 'N/A'}")
        print(f"Title: {title[0] if title else 'N/A'}")
        print(f"Duration: {duration[0] if duration else 'N/A'}")
        print(f"ClickThrough: {click_url[0] if click_url else 'N/A'}")
        print(f"Media URLs: {media_urls}")
        print(f"Channel Name: {channel_name}")
        print("-" * 40)

        # --- Insert one row per ad ---
        cur.execute("""
            INSERT INTO vast_ads (call_number, ad_id, creative_id, title, duration, clickthrough, media_urls, channel_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i + 1,
            ad_id,
            creative_id,
            title[0] if title else None,
            duration[0] if duration else None,
            click_url[0] if click_url else None,
            json.dumps(media_urls),
            channel_name
        ))

    time.sleep(1)

# --- Finalize DB ---
conn.commit()
conn.close()
print("✅ Data saved to vast_ads.db")
