import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import ssl
import os
import sys
import datetime
import threading
import time

# --- CONFIGURATION ---
TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"  # For actions (create, stats)
URL_INFO = "https://api.ads.com"    # For info (offers, links)

# --- SSL CONTEXT (Unsafe for dev) ---
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# --- GLOBAL CACHE ---
local_cache = {
    "offers": [],
    "articles": [],
    "last_sync": "Never",
    "sync_log": []
}

SYNC_INTERVAL = 300 # 5 minutes

def api_req(domain, endpoint, data=None):
    url = f"{domain}{endpoint}"
    try:
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        if data is not None:
            req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
        else:
            req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            raw = r.read().decode()
            # Handle broken API returning PHP notices before JSON
            if "{" in raw:
                raw_json = raw[raw.find("{"):]
                return json.loads(raw_json)
            return json.loads(raw)
    except Exception as e:
        print(f"API Error ({endpoint}): {e}")
        return {"status": "error", "message": str(e), "raw": raw if 'raw' in locals() else ""}

def scraper_loop():
    """Periodically refresh offers and articles in the background."""
    # Load from config.json on first run
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)
                local_cache["offers"] = config_data.get("offers", [])
                local_cache["articles"] = config_data.get("articles", [])
                print(f">>> Loaded {len(local_cache['offers'])} offers and {len(local_cache['articles'])} articles from config.json")
    except Exception as e:
        print(f"Config load error: {e}")
    
    while True:
        try:
            print(">>> Background Scraper: Checking API for updates...")
            
            # --- SCRAPE OFFERS ---
            # We found that /panel/offer/list returns a filter structure with all offers!
            r = api_req(URL_ACTION, "/panel/offer/list")
            if r and r.get("status") == "ok":
                try:
                    # Structure: data -> list -> [0] -> values -> [{key, value}, ...]
                    filters = r.get("data", {}).get("list", [])
                    offers_filter = next((f for f in filters if f.get("name") == "offer"), None)
                    
                    if offers_filter and "values" in offers_filter:
                        found = []
                        for item in offers_filter["values"]:
                            found.append({"id": item["key"], "name": item["value"]})
                        
                        if found:
                            local_cache["offers"] = found
                            print(f">>> Updated offers from API: {len(found)} items (Auto-discovered)")
                except Exception as e:
                    print(f"Offer parse error: {e}")

            # Fallback to config if API returned nothing
            if not local_cache["offers"] and os.path.exists("config.json"):
                 try: 
                    with open("config.json", "r", encoding="utf-8") as f:
                        local_cache["offers"] = json.load(f).get("offers", [])
                 except: pass

            # --- SCRAPE SITES/ARTICLES ---
            # Try finding sites (similar logic might apply, but let's stick to /panel/sites first)
            for domain in [URL_INFO, URL_ACTION]:
                r = api_req(domain, "/panel/sites", {"limit":500})
                if r and r.get("status") == "ok":
                    data = r.get("data", {}).get("list", []) or []
                    if data:
                        local_cache["articles"] = [{"id": i.get("site_key") or i.get("id"), "name": i.get("title") or i.get("name")} for i in data if i.get("site_key") or i.get("id")]
                        print(f">>> Updated articles from API: {len(local_cache['articles'])} items")
                        break
        except Exception as e:
            print(f"Scraper Error: {e}")
        
        time.sleep(3600) # Once per hour is enough for offers

def syncer_loop():
    """Background loop to sync with Skro."""
    # Load sync state to prevent duplicates
    # Support for Persistent Volume (Railway/Docker)
    storage_dir = os.environ.get("STORAGE_PATH", ".")
    if not os.path.exists(storage_dir):
        try: os.makedirs(storage_dir)
        except: pass
        
    sync_state = {}
    state_file = os.path.join(storage_dir, "sync_state.json")
    
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f: sync_state = json.load(f)
        except: pass

    while True:
        try:
            print(">>> Auto-Sync: Fetching stats by ClickID (sub1)...")
            today = datetime.datetime.now().strftime("%d.%m.%Y")
            # CRITICAL: Docs say "campaign - By subid". 
            # So we use groups=['campaign'] to get the stats per subid.
            payload = {
                "date_start": today, "date_end": today,
                "groups": ["campaign"], 
                "timezone": "Europe/Kyiv",
                "limit": 500
            }
            resp = api_req(URL_ACTION, "/panel/stats", payload)
            
            count = 0
            updated_state = False
            
            if resp and resp.get("status") == "ok":
                lst = resp.get("data", {}).get("list", []) or []
                for row in lst:
                    # sub1 is our clickid
                    groups = row.get("groups")
                    clickid = None
                    if isinstance(groups, list) and len(groups) > 0:
                        clickid = groups[0]
                    elif isinstance(groups, dict):
                         clickid = groups.get("sub1")
                    
                    if not clickid:
                        # Fallback parsing
                        clickid = row.get("sub1") or row.get("group")
                        
                    current_rev = float(row.get("revenue", 0))
                    
                    if clickid and current_rev > 0:
                        prev_rev = sync_state.get(clickid, 0.0)
                        
                        # Only send if we have NEW revenue
                        if current_rev > prev_rev:
                            delta = current_rev - prev_rev
                            
                            # Sanity check: don't sync tiny float diffs
                            if delta > 0.001:
                                # Generate unique transaction ID for this partial update (upsell)
                                txid = f"{clickid}-{int(time.time())}"
                                pb_url = f"https://skrotrack.com/postback?clickId={clickid}&payout={delta}&transactionId={txid}&status=approved&txt=autosync"
                                try:
                                    urllib.request.urlopen(pb_url, context=ctx)
                                    count += 1
                                    # Update state
                                    sync_state[clickid] = current_rev
                                    updated_state = True
                                    log_msg = f"[{datetime.datetime.now().strftime('%H:%M')}] Synced {clickid} (+${delta:.2f})"
                                    local_cache["sync_log"].insert(0, log_msg)
                                    print(f"   -> {log_msg}")
                                except Exception as e:
                                    print(f"   -> Skro Req Failed: {e}")
            
            if updated_state:
                # Save state to file
                try:
                    with open(state_file, "w") as f:
                        json.dump(sync_state, f)
                except: pass
            
            local_cache["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            local_cache["sync_log"] = local_cache["sync_log"][:50] 
            if count > 0:
                print(f">>> Auto-Sync Finished: {count} new conversions synced.")
            else:
                print(">>> Auto-Sync: No new conversions.")
                
        except Exception as e:
            print(f"Syncer Error: {e}")
        
        time.sleep(SYNC_INTERVAL)

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/create_link":
            self._handle_create()
        elif path == "/api/list_links":
            self._handle_history()
        elif path == "/api/get_stats":
            self._handle_get_stats()
        elif path == "/api/sync":
            self._handle_manual_sync()
        else:
            self.send_error(404)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/data":
            self._send_json({"offers": local_cache["offers"], "articles": local_cache["articles"]})
        elif parsed.path == "/api/status":
            self._send_json({"last_sync": local_cache["last_sync"], "log": local_cache["sync_log"]})
        elif parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open("dashboard.html", "rb") as f: self.wfile.write(f.read())
        else:
            super().do_GET()

    def _handle_create(self):
        l = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(l))
        
        # Parse keywords and ensure minimum 3
        kw_list = [k.strip() for k in data.get("keywords", "").split(",") if k.strip()]
        # Pad with defaults if less than 3
        while len(kw_list) < 3:
            kw_list.append(f"keyword{len(kw_list)+1}")
        
        # Base payload with common fields
        # "name", "offer", "site_key", "title", "referrerAdCreative", "keywords", "postback"
        site_val = data.get("article") or "default_site"
        payload = {
            "name": data.get("name", ""),
            "offer": data.get("offer", ""),
            "site_key": site_val,
            "direct": site_val, # REQUIRED by API backend (undocumented legacy prop?)
            "title": data.get("title") or data.get("name", ""),
            "referrerAdCreative": data.get("referrerAdCreative") or "organic",
            "keywords": kw_list,
            "postback": data.get("postback_type", "s2s")
        }

        # Type-specific fields based on docs examples
        if payload["postback"] == "s2s":
             # For S2S, 'pixel_token' holds the Postback URL
             # Example input only showed pixel_token
             pt = data.get("pixel_token", "")
             if not pt:
                 pt = "https://skrotrack.com/postback?clickId={clickid}&payout={revenue}"
             payload["pixel_token"] = pt
             
             # Optionally send pixel_event if you want defaults, but example omitted it for input.
             # We will send 'lead' just in case, or omit if strictly following input list.
             # Response example showed 'pixel_event': 'lead', so better to send it.
             payload["pixel_event"] = "lead"

        elif payload["postback"] in ["tiktok", "facebook"]:
            # TikTok/FB need all pixel fields
            payload["pixel_id"] = data.get("pixel_id", "")
            payload["pixel_token"] = data.get("pixel_token", "") # Access Token
            payload["pixel_event"] = data.get("pixel_event", "Lead")

        # Fallback for other potential types (should match TikTok structure usually)
        else:
            payload["pixel_id"] = data.get("pixel_id", "")
            payload["pixel_token"] = data.get("pixel_token", "")
            payload["pixel_event"] = data.get("pixel_event", "")

        resp = api_req(URL_ACTION, "/panel/link_create", payload)
        if resp and resp.get("status") == "ok":
            d = resp.get("data", {})
            lid = d.get("link_id") or d.get("link_facebook_id") or d.get("link_tiktok_id")
            url = d.get("url", "")
            
            # Append sub1 ALWAYS to support Skro Auto-Sync for all types
            # (Sync relies on sub1 containing the clickID)
            if "sub1=" not in url:
                url += ("&" if "?" in url else "?") + "sub1={clickid}"
                
            self._send_json({"status": "ok", "url": url, "api_id": lid, "api_status": d.get("status")})
        else:
            self._send_json({"status": "error", "debug": resp})

    def _handle_history(self):
        resp = api_req(URL_INFO, "/panel/links", {"page": 1})
        if resp and resp.get("status") == "ok":
            lst = resp.get("data", {}).get("list", []) or []
            normalized = []
            for item in lst[:10]: # Check last 10
                normalized.append({
                    "date": item.get("date_create", ""),
                    "id": item.get("link_id") or item.get("id", ""),
                    "name": item.get("name", ""),
                    "offer": item.get("offer", ""),
                    "url": item.get("url", "")
                })
            self._send_json({"links": normalized})
        else:
            self._send_json({"links": []})

    def _handle_get_stats(self):
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        payload = {"date_start": today, "date_end": today, "timezone": "Europe/Kyiv"}
        resp = api_req(URL_ACTION, "/panel/stats", payload)
        self._send_json(resp)

    def _handle_manual_sync(self):
        # Trigger one iteration of syncer logic in a new thread to avoid blocking
        threading.Thread(target=syncer_loop, daemon=True).start()
        self._send_json({"status": "triggered", "message": "Sync started in background"})

    def _send_json(self, d):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(d).encode('utf-8'))

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8000))  # Railway provides PORT env var
    socketserver.TCPServer.allow_reuse_address = True
    
    # Start threads
    threading.Thread(target=scraper_loop, daemon=True).start()
    threading.Thread(target=syncer_loop, daemon=True).start()
    
    print(f"=== ADW INTEGRATION SERVER STARTED ===")
    print(f"Port: {PORT}")
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), APIHandler) as httpd:  # Bind to 0.0.0.0 for Railway
            httpd.serve_forever()
    except Exception as e:
        print(f"FATAL SERVER ERROR: {e}")
        sys.exit(1)
