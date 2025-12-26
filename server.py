import http.server
import socketserver
import json
import urllib.parse
import urllib.request
import urllib.error
import ssl
import os
import sys
import datetime
import threading
import time

# --- CONFIGURATION ---
TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"  # Stats, Create
URL_INFO   = "https://api.ads.com"  # List Links, Get Link

# SYNC CONFIG
SYNC_INTERVAL = 300 # 5 minutes
local_cache = {"offers": [], "articles": [], "last_sync": "Never", "sync_log": []}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api_req(domain, endpoint, params=None, method='POST'):
    url = f"{domain}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        if params is not None:
             req.data = json.dumps(params).encode('utf-8')
        
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[API Error] {url}: {e}")
        return {"status": "error", "message": str(e)}

def scraper_loop():
    """Periodically refresh offers and articles in the background."""
    while True:
        try:
            print(">>> Background Scraper: Updating Offers/Articles...")
            # Try finding offers on both domains
            for domain in [URL_INFO, URL_ACTION]:
                ep_variants = ["/panel/offers", "/panel/list_offers", "/panel/all_offers"]
                found = []
                for ep in ep_variants:
                    r = api_req(domain, ep, {"page":1, "limit":500})
                    if not r or r.get("status") != "ok": r = api_req(domain, ep, {})
                    
                    if r and r.get("status") == "ok":
                        data = r.get("data", {}).get("list", []) or r.get("data") or []
                        if isinstance(data, list):
                            for i in data:
                                oid = i.get("id") or i.get("offer_id") or i.get("name")
                                nm = i.get("name") or i.get("title") or oid
                                if oid: found.append({"id":oid, "name":nm})
                            if found: 
                                local_cache["offers"] = found
                                break
                if found: break

            # Try finding sites
            for domain in [URL_INFO, URL_ACTION]:
                r = api_req(domain, "/panel/sites", {"limit":500})
                if r and r.get("status") == "ok":
                    data = r.get("data", {}).get("list", []) or []
                    if data:
                        local_cache["articles"] = [{"id": i.get("site_key") or i.get("id"), "name": i.get("title") or i.get("name")} for i in data if i.get("site_key") or i.get("id")]
                        break
        except Exception as e:
            print(f"Scraper Error: {e}")
        
        time.sleep(3600) # Once per hour is enough for offers

def syncer_loop():
    """Background thread to sync stats from Adw to Skro."""
    while True:
        try:
            print(f">>> Auto-Sync: Checking conversions...")
            today = datetime.datetime.now().strftime("%d.%m.%Y")
            payload = {
                "date_start": today, "date_end": today,
                "groups": ["campaign"], # This is subid/clickid
                "timezone": "Europe/Kyiv"
            }
            resp = api_req(URL_ACTION, "/panel/stats", payload)
            
            count = 0
            if resp and resp.get("status") == "ok":
                lst = resp.get("data", {}).get("list", []) or []
                for row in lst:
                    subid = row.get("groups", [None])[0] or row.get("group")
                    rev = float(row.get("revenue", 0))
                    if subid and rev > 0:
                        pb_url = f"https://s2s.skro.eu/postback?clickid={subid}&payout={rev}&txt=autosync"
                        try:
                            urllib.request.urlopen(pb_url, context=ctx)
                            count += 1
                            local_cache["sync_log"].insert(0, f"[{datetime.datetime.now().strftime('%H:%M')}] Synced {subid} (${rev})")
                        except: pass
            
            local_cache["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            local_cache["sync_log"] = local_cache["sync_log"][:20] # Keep 20 entries
            print(f">>> Auto-Sync Finished: {count} events.")
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
        
        # Doc fields mapping - use title from data or fallback to name
        payload = {
            "name": data.get("name", ""),
            "offer": data.get("offer", ""),
            "title": data.get("title") or data.get("name", ""),
            "postback": data.get("postback_type", "s2s"),
            "keywords": kw_list,
            "pixel_id": data.get("pixel_id", ""),
            "pixel_token": data.get("pixel_token", ""),
            "pixel_event": data.get("pixel_event", ""),
            "referrerAdCreative": data.get("referrerAdCreative") or "organic",  # Required by API!
            "direct": data.get("article") or "default_site"  # API requires non-empty value!
        }
        
        # Skro default for S2S
        if payload["postback"] == "s2s":
            if not payload["pixel_token"]: payload["pixel_token"] = "https://s2s.skro.eu/postback?clickid={clickid}&payout={revenue}"
            if not payload["pixel_event"]: payload["pixel_event"] = "lead"

        resp = api_req(URL_ACTION, "/panel/link_create", payload)
        if resp and resp.get("status") == "ok":
            d = resp.get("data", {})
            lid = d.get("link_id") or d.get("link_facebook_id") or d.get("link_tiktok_id")
            url = d.get("url", "")
            # Append subid for Skro
            if payload["postback"] == "s2s":
                url += ("&" if "?" in url else "?") + "sub1={clickid}"
            self._send_json({"status": "ok", "url": url, "api_id": lid, "api_status": d.get("status")})
        else:
            self._send_json({"status": "error", "debug": resp})

    def _handle_history(self):
        resp = api_req(URL_INFO, "/panel/links", {"page": 1})
        links = []
        if resp and resp.get("status") == "ok":
            lst = resp.get("data", {}).get("list", []) or []
            for i in lst:
                links.append({"id": i.get("link_id"), "name": i.get("name"), "url": i.get("url"), "offer": i.get("offer"), "date": i.get("date_create")})
        self._send_json({"status": "ok", "links": links})

    def _handle_get_stats(self):
        """Fetch raw stats from Adw API for display in dashboard."""
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        payload = {
            "date_start": today,
            "date_end": today,
            "groups": ["offer", "campaign"],
            "timezone": "Europe/Kyiv"
        }
        resp = api_req(URL_ACTION, "/panel/stats", payload)
        self._send_json(resp if resp else {"status": "error", "message": "Stats fetch failed"})

    def _handle_manual_sync(self):
        """Manually trigger sync and return count."""
        try:
            today = datetime.datetime.now().strftime("%d.%m.%Y")
            payload = {
                "date_start": today, "date_end": today,
                "groups": ["campaign"],
                "timezone": "Europe/Kyiv"
            }
            resp = api_req(URL_ACTION, "/panel/stats", payload)
            count = 0
            if resp and resp.get("status") == "ok":
                lst = resp.get("data", {}).get("list", []) or []
                for row in lst:
                    subid = row.get("groups", [None])[0] or row.get("group")
                    rev = float(row.get("revenue", 0))
                    if subid and rev > 0:
                        pb_url = f"https://s2s.skro.eu/postback?clickid={subid}&payout={rev}&txt=manualsync"
                        try:
                            urllib.request.urlopen(pb_url, context=ctx)
                            count += 1
                        except: pass
            self._send_json({"status": "ok", "synced": count})
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)})

    def _send_json(self, d):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
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
