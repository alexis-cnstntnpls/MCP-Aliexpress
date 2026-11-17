import json
import re
from curl_cffi import requests

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

s = requests.Session(impersonate="chrome124")
s.cookies.set("aep_usuc_f", "region=FR&b_locale=fr_FR&site=fra&c_tp=EUR", domain=".aliexpress.com")

# Let's test a real product ID from earlier search: 1005010044071881
url = "https://fr.aliexpress.com/item/1005010044071881.html"
resp = s.get(url, headers=headers, timeout=15)
print(f"Status: {resp.status_code}, URL: {resp.url}, Length: {len(resp.text)}")

# Check for data blocks in HTML
matches = re.findall(r'window\.runParams\s*=\s*(\{.+?\});', resp.text)
print(f"window.runParams matches: {len(matches)}")

matches_dida = re.findall(r'window\._dida_config_\s*=', resp.text)
print(f"window._dida_config_ matches: {len(matches_dida)}")

# Check for other JSON data blobs
data_matches = re.findall(r'data:\s*(\{.+?\})\s*,\s*csrfToken', resp.text)
print(f"data:...csrfToken matches: {len(data_matches)}")

# Save a sample to inspect
with open("/home/alexis/MCP-AliExpress/prototype/item_sample.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("Saved sample to /home/alexis/MCP-AliExpress/prototype/item_sample.html")
