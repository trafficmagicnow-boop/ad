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
import hashlib
import uuid
import time as time_module

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db(db_path):
    """Initialize the SQLite database with required tables and indexes."""
    conn = sqlite3.connect(db_path, timeout=30.0)
    try:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE NOT NULL,
                     password_hash TEXT NOT NULL,
                     role TEXT DEFAULT 'user',
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        
        # Campaigns table (track user's created links)
        c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER NOT NULL,
                     name TEXT,
                     link_id TEXT,
                     offer TEXT,
                     site TEXT,
                     url TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY(user_id) REFERENCES users(id)
                     )''')
        
        # Sessions table
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                     token TEXT PRIMARY KEY,
                     user_id INTEGER NOT NULL,
                     expires_at REAL,
                     FOREIGN KEY(user_id) REFERENCES users(id)
                     )''')
        
        # Table to track total revenue per Click ID (deduplication)
        c.execute('''CREATE TABLE IF NOT EXISTS conversions (
                     click_id TEXT PRIMARY KEY,
                     total_rev REAL DEFAULT 0,
                     last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        # Table to log sync events (history)
        c.execute('''CREATE TABLE IF NOT EXISTS sync_log (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     click_id TEXT,
                     amount REAL,
                     tx_id TEXT,
                     status TEXT,
                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        
        # Create indexes for performance at scale
        c.execute('''CREATE INDEX IF NOT EXISTS idx_sync_log_clickid ON sync_log(click_id)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp ON sync_log(timestamp)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_conversions_updated ON conversions(last_updated)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)''')
        
        # Create default admin user if not exists
        c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if c.fetchone()[0] == 0:
            admin_hash = hash_password("admin123")
            c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                     ("admin", admin_hash, "admin"))
            print(">>> Created default admin user (username: admin, password: admin123)")
        
        conn.commit()
    finally:
        conn.close()

def create_session(db_path, user_id):
    """Create a new session for user"""
    token = str(uuid.uuid4())
    expires_at = time_module.time() + 86400  # 24 hours
    
    with sqlite3.connect(db_path, timeout=30.0) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                 (token, user_id, expires_at))
        conn.commit()
    return token

def validate_session(db_path, token):
    """Check if session is valid and not expired"""
    if not token:
        return None
    
    with sqlite3.connect(db_path, timeout=30.0) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, expires_at FROM sessions WHERE token = ?", (token,))
        res = c.fetchone()
        
        if not res:
            return None
        
        user_id, expires_at = res
        if time_module.time() > expires_at:
            # Session expired
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        
        return user_id

def get_user_from_session(db_path, token):
    """Get user object from session token"""
    user_id = validate_session(db_path, token)
    if not user_id:
        return None
    
    with sqlite3.connect(db_path, timeout=30.0) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        res = c.fetchone()
        
        if res:
            return {"id": res[0], "username": res[1], "role": res[2]}
    return None

def cleanup_expired_sessions(db_path):
    """Remove expired sessions"""
    with sqlite3.connect(db_path, timeout=30.0) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE expires_at < ?", (time_module.time(),))
        conn.commit()

import sqlite3

# --- CACHE DECORATORS ---
DASHBOARD_CACHE = b""
def init_dashboard_cache():
    global DASHBOARD_CACHE
    try:
        with open("dashboard.html", "rb") as f:
            DASHBOARD_CACHE = f.read()
    except Exception as e:
        print(f"Error caching dashboard: {e}")
        DASHBOARD_CACHE = b"Error loading dashboard"

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
    "pixel_events": [],
    "last_sync": "Never",
    "sync_log": [],
    "history": [],
    "stats": {"status": "ok", "total_campaigns": 0, "total_conversions": 0}
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
        
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
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
                    
                    # --- SCRAPE PIXEL EVENTS ---
                    # Same endpoint also contains pixel_event filter
                    events_filter = next((f for f in filters if f.get("name") == "pixel_event"), None)
                    if events_filter and "values" in events_filter:
                        events_found = []
                        for item in events_filter["values"]:
                            events_found.append({"id": item["key"], "name": item["value"]})
                        
                        if events_found:
                            local_cache["pixel_events"] = events_found
                            print(f">>> Updated pixel events from API: {len(events_found)} items (Auto-discovered)")
                except Exception as e:
                    print(f"Offer/Events parse error: {e}")

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
            # --- SCRAPE HISTORY ---
            h = api_req(URL_INFO, "/panel/links", {"page": 1})
            if h and h.get("status") == "ok":
                lst = h.get("data", {}).get("list", []) or []
                norm = []
                for item in lst[:15]:
                    norm.append({
                        "date": item.get("date_create", ""),
                        "id": item.get("link_id") or item.get("id", ""),
                        "name": item.get("name", ""),
                        "offer": item.get("offer", ""),
                        "url": item.get("url", "")
                    })
                local_cache["history"] = norm
                print(f">>> Updated history cache: {len(norm)} items")

            # --- SCRAPE STATS ---
            today = datetime.datetime.now().strftime("%d.%m.%Y")
            s = api_req(URL_ACTION, "/panel/stats", {"date_start": today, "date_end": today, "timezone": "Europe/Kyiv"})
            if s and s.get("status") == "ok":
                local_cache["stats"] = s
                print(">>> Updated stats cache")

        except Exception as e:
            print(f"Scraper Error: {e}")
        
        time_module.sleep(300) # Faster refresh for stats/history (5 mins)


def syncer_loop():
    """Background loop to sync with Skro using SQLite for persistence."""
    # Support for Persistent Volume (Railway/Docker)
    storage_dir = os.environ.get("STORAGE_PATH", ".")
    if not os.path.exists(storage_dir):
        try: os.makedirs(storage_dir)
        except: pass
        
    db_path = os.path.join(storage_dir, "adw.db")
    
    # Initialize DB (run once on start in thread)
    try:
        init_db(db_path)
        print(f">>> Database initialized at: {db_path}")
    except Exception as e:
        print(f"DB Init Failed: {e}")

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
            
            if resp and resp.get("status") == "ok":
                lst = resp.get("data", {}).get("list", []) or []
                
                # Connect to DB for this sync cycle
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
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
                            # Check DB for previous total
                            cursor.execute("SELECT total_rev FROM conversions WHERE click_id = ?", (clickid,))
                            res = cursor.fetchone()
                            prev_rev = res[0] if res else 0.0
                            
                            # Only send if we have NEW revenue
                            if current_rev > prev_rev:
                                delta = current_rev - prev_rev
                                
                                # Sanity check: don't sync tiny float diffs
                                if delta > 0.001:
                                    # Generate unique transaction ID for this partial update (upsell)
                                    txid = f"{clickid}-{int(time_module.time())}"
                                    pb_url = f"https://skrotrack.com/postback?clickId={clickid}&payout={delta}&transactionId={txid}&status=approved&txt=autosync"
                                    try:
                                        urllib.request.urlopen(pb_url, context=ctx)
                                        count += 1
                                        
                                        # Update state in DB
                                        cursor.execute("INSERT OR REPLACE INTO conversions (click_id, total_rev) VALUES (?, ?)", (clickid, current_rev))
                                        
                                        # Log to DB log
                                        cursor.execute("INSERT INTO sync_log (click_id, amount, tx_id, status) VALUES (?, ?, ?, ?)", (clickid, delta, txid, "synced"))
                                        
                                        log_msg = f"[{datetime.datetime.now().strftime('%H:%M')}] Synced {clickid} (+${delta:.2f})"
                                        local_cache["sync_log"].insert(0, log_msg)
                                        print(f"   -> {log_msg}")
                                        
                                        conn.commit() # Commit transaction immediately
                                    except Exception as e:
                                        print(f"   -> Skro Req Failed: {e}")
            
            local_cache["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            local_cache["sync_log"] = local_cache["sync_log"][:50] 
            if count > 0:
                print(f">>> Auto-Sync Finished: {count} new conversions synced.")
            else:
                print(">>> Auto-Sync: No new conversions.")
                
        except Exception as e:
            print(f"Syncer Error: {e}")
        
        time_module.sleep(SYNC_INTERVAL)

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        
        # Auth endpoints
        if path == "/api/login":
            self._handle_login()
        elif path == "/api/logout":
            self._handle_logout()
        elif path == "/api/admin/users/create":
            self._handle_admin_users_create()
        elif path == "/api/admin/users/delete":
            self._handle_admin_users_delete()
        elif path == "/api/create_link":
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
        if parsed.path == "/api/me":
            self._handle_me()
        elif parsed.path == "/api/admin/users":
            self._handle_admin_users_list()
        elif parsed.path == "/api/data":
            self._send_json({
                "offers": local_cache["offers"], 
                "articles": local_cache["articles"],
                "pixel_events": local_cache["pixel_events"]
            })
        elif parsed.path == "/api/status":
            self._send_json({"last_sync": local_cache["last_sync"], "log": local_cache["sync_log"]})
        elif parsed.path == "/" or parsed.path == "/index.html" or parsed.path == "/dashboard.html":
            # Check if user is authenticated
            storage_dir = os.environ.get("STORAGE_PATH", ".")
            db_path = os.path.join(storage_dir, "adw.db")
            token = self._get_session_token()
            user = get_user_from_session(db_path, token)
            
            if user:
                # Serve dashboard
                # Clean v3.0 serving
                if not os.path.exists("dashboard.html"):
                    self.send_error(404, "Dashboard file not found")
                    return
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                # Ensure we read the file from disk every time for now
                self.wfile.write(DASHBOARD_CACHE)
            else:
                # Serve login page
                if not os.path.exists("login.html"):
                    self.send_error(404, "Login page not found")
                    return
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                with open("login.html", "rb") as f: self.wfile.write(f.read())
        else:
            super().do_GET()


    def _get_session_token(self):
        """Extract session token from cookie"""
        cookie_header = self.headers.get('Cookie', '')
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if cookie.startswith('session='):
                return cookie.split('=', 1)[1]
        return None

    def _handle_admin_users_list(self):
        """List all users (Admin only)"""
        if not self._check_admin(): return
        
        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, role, created_at FROM users")
            users = [{"id": r[0], "username": r[1], "role": r[2], "created_at": r[3]} for r in c.fetchall()]
            
        self._send_json({"status": "ok", "users": users})

    def _handle_admin_users_create(self):
        """Create new user (Admin only)"""
        if not self._check_admin(): return

        l = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(l))
        
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        role = data.get("role", "user")
        
        if not username or not password:
            self._send_json({"status": "error", "message": "Username and password required"})
            return

        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        
        try:
            password_hash = hash_password(password)
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                         (username, password_hash, role))
                conn.commit()
            self._send_json({"status": "ok", "message": "User created"})
        except sqlite3.IntegrityError:
            self._send_json({"status": "error", "message": "Username already exists"})
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)})

    def _handle_admin_users_delete(self):
        """Delete user (Admin only)"""
        if not self._check_admin(): return

        l = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(l))
        user_id = data.get("user_id")
        
        if not user_id:
             self._send_json({"status": "error", "message": "User ID required"})
             return
             
        # Prevent deleting self or admin? Maybe just prevent deleting the last admin, but let's keep it simple.
        # Prevent deleting ID 1 (default admin) usually a good idea
        if int(user_id) == 1:
             self._send_json({"status": "error", "message": "Cannot delete default admin"})
             return

        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
        self._send_json({"status": "ok", "message": "User deleted"})

    def _check_admin(self):
        """Helper to check if current user is admin"""
        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        token = self._get_session_token()
        user = get_user_from_session(db_path, token)
        
        if not user or user["role"] != "admin":
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Admin access required"}).encode('utf-8'))
            return False
        return True

    def _handle_login(self):
        """Handle login request"""
        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        
        l = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(l))
        
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        if not username or not password:
            self._send_json({"status": "error", "message": "Username and password required"})
            return
        
        # Check credentials
        password_hash = hash_password(password)
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, role FROM users WHERE username = ? AND password_hash = ?", 
                     (username, password_hash))
            res = c.fetchone()
            
            if not res:
                self._send_json({"status": "error", "message": "Invalid credentials"})
                return
            
            user_id, role = res
        
        # Create session
        token = create_session(db_path, user_id)
        
        # Send response with cookie
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Set-Cookie', f'session={token}; Path=/; Max-Age=86400; HttpOnly; SameSite=Strict')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "user": {"id": user_id, "username": username, "role": role}
        }).encode('utf-8'))

    def _handle_logout(self):
        """Handle logout request"""
        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        
        token = self._get_session_token()
        if token:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Set-Cookie', 'session=; Path=/; Max-Age=0')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))

    def _handle_me(self):
        """Get current user from session"""
        storage_dir = os.environ.get("STORAGE_PATH", ".")
        db_path = os.path.join(storage_dir, "adw.db")
        
        token = self._get_session_token()
        user = get_user_from_session(db_path, token)
        
        if user:
            self._send_json({"status": "ok", "user": user})
        else:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Not authenticated"}).encode('utf-8'))

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
        self._send_json({"status": "ok", "history": local_cache["history"]})

    def _handle_get_stats(self):
        self._send_json(local_cache["stats"])

    def _handle_manual_sync(self):
        # Run a single sync iteration without spawning new infinite loop
        def sync_once():
            storage_dir = os.environ.get("STORAGE_PATH", ".")
            db_path = os.path.join(storage_dir, "adw.db")
            try:
                today = datetime.datetime.now().strftime("%d.%m.%Y")
                payload = {
                    "date_start": today, "date_end": today,
                    "groups": ["campaign"], 
                    "timezone": "Europe/Kyiv",
                    "limit": 500
                }
                resp = api_req(URL_ACTION, "/panel/stats", payload)
                count = 0
                if resp and resp.get("status") == "ok":
                    lst = resp.get("data", {}).get("list", []) or []
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        for row in lst:
                            groups = row.get("groups")
                            clickid = None
                            if isinstance(groups, list) and len(groups) > 0:
                                clickid = groups[0]
                            elif isinstance(groups, dict):
                                clickid = groups.get("sub1")
                            if not clickid:
                                clickid = row.get("sub1") or row.get("group")
                            current_rev = float(row.get("revenue", 0))
                            if clickid and current_rev > 0:
                                cursor.execute("SELECT total_rev FROM conversions WHERE click_id = ?", (clickid,))
                                res = cursor.fetchone()
                                prev_rev = res[0] if res else 0.0
                                if current_rev > prev_rev:
                                    delta = current_rev - prev_rev
                                    if delta > 0.001:
                                        txid = f"{clickid}-{int(time_module.time())}"
                                        pb_url = f"https://skrotrack.com/postback?clickId={clickid}&payout={delta}&transactionId={txid}&status=approved&txt=manual"
                                        try:
                                            urllib.request.urlopen(pb_url, context=ctx)
                                            count += 1
                                            cursor.execute("INSERT OR REPLACE INTO conversions (click_id, total_rev) VALUES (?, ?)", (clickid, current_rev))
                                            cursor.execute("INSERT INTO sync_log (click_id, amount, tx_id, status) VALUES (?, ?, ?, ?)", (clickid, delta, txid, "manual"))
                                            conn.commit()
                                        except: pass
                print(f"Manual sync: {count} conversions")
            except Exception as e:
                print(f"Manual sync error: {e}")
        
        threading.Thread(target=sync_once, daemon=True).start()
        self._send_json({"status": "triggered", "message": "One-time sync started"})

    def _send_json(self, d):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(json.dumps(d).encode('utf-8'))

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8000))  # Railway provides PORT env var
    socketserver.TCPServer.allow_reuse_address = True
    
    # --- STARTUP DIAGNOSTICS ---
    print(f"=== SYSTEM STARTUP DIAGNOSIS ===")
    cwd = os.getcwd()
    print(f"CWD: {cwd}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script Dir: {script_dir}")
    
    print(f"Script Dir: {script_dir}")
    
    # Startup check
    dash_path = os.path.join(script_dir, "dashboard.html")
    if os.path.exists(dash_path):
        with open(dash_path, "rb") as f:
            content = f.read()
            import hashlib
            h = hashlib.md5(content).hexdigest()
            print(f"✅ Dashboard loaded. MD5: {h}")
    else:
        print(f"❌ FATAL: dashboard.html missing at {dash_path}")
    # ---------------------------
    # ---------------------------

    # Start threads
    init_dashboard_cache()
    threading.Thread(target=scraper_loop, daemon=True).start()
    threading.Thread(target=syncer_loop, daemon=True).start()
    
    print(f"=== ADW INTEGRATION SERVER STARTED ===")
    print(f"Port: {PORT}")
    try:
        # Change dir to script dir to ensure relative paths work if needed
        os.chdir(script_dir)
        # Use ThreadingTCPServer to prevent UI lag during long-running operations (like sync)
        class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            pass

        socketserver.TCPServer.allow_reuse_address = True
        with ThreadedTCPServer(("0.0.0.0", PORT), APIHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"FATAL SERVER ERROR: {e}")
        sys.exit(1)
