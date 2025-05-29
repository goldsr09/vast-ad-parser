# parser_display.py

import requests
from lxml import etree
from urllib.parse import urlparse, parse_qs

def parse_vast(url):
    
    call_number = 2  # You can modify or remove this if not needed

    headers = {
        "User-Agent": "Roku/DVP-14.5 (14.5.4.5934-46)"
    }

    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    csid = query_params.get("csid", [""])[0]
    csid_parts = csid.split("/")
    channel_name = csid_parts[1] if len(csid_parts) >= 2 else None

    response = requests.get(url, headers=headers)
    if response.status_code != 200 or not response.content.strip():
        return [{"error": f"❌ Request failed with status {response.status_code}"}]

    parser = etree.XMLParser(recover=True)
    try:
        tree = etree.fromstring(response.content, parser=parser)
    except etree.XMLSyntaxError as e:
        return [{"error": f"❌ XML parse error: {e}"}]

    results = []
    ads = tree.xpath("//Ad")
    for ad in ads:
        ad_id = ad.get("id", "N/A")
        title = ad.xpath(".//AdTitle/text()")
        duration = ad.xpath(".//Duration/text()")
        click_url = ad.xpath(".//ClickThrough/text()")
        creative_id = ad.xpath(".//Creative/@id")
        creative_id = creative_id[0] if creative_id else None
        media_files = ad.xpath(".//MediaFile")
        media_urls = [mf.text.strip() for mf in media_files if mf.text]

        results.append({
            "call_number": call_number,
            "ad_id": ad_id,
            "creative_id": creative_id,
            "title": title[0] if title else None,
            "duration": duration[0] if duration else None,
            "clickthrough": click_url[0] if click_url else None,
            "media_urls": media_urls,
            "channel_name": channel_name
        })

    return results
