import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import sys
import datetime
import time
import csv
import os

# --- CONFIGURATION ---
ADW_API_TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
ADW_BASE_URL = "https://api.adw.net" 

# SKRO Postback Base URL
SKRO_POSTBACK_BASE = "https://s2s.skro.eu/postback"

class AdwClient:
    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def _request(self, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        try:
            req = urllib.request.Request(url, headers=self.headers)
            if data:
                json_data = json.dumps(data).encode('utf-8')
                req.data = json_data
                req.method = 'POST'
            
            with urllib.request.urlopen(req, context=self.ctx) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"  [API Error] {e.code}: {e.read().decode('utf-8')}")
            return None
        except Exception as e:
            print(f"  [Error] {str(e)}")
            return None

    def create_link(self, name, offer, keywords):
        skro_pb = "https://s2s.skro.eu/postback?clickid={clickid}&payout={revenue}"
        payload = {
            "name": name,
            "offer": offer,
            "title": name,
            "keywords": keywords,
            "postback": "s2s",
            "pixel_token": skro_pb,
            "pixel_event": "lead"
        }
        return self._request("/panel/link_create", payload)

    def get_conversion_stats(self, date_from, date_to):
        payload = {
            "date_start": date_from,
            "date_end": date_to,
            "groups": ["campaign"], # grouped by subid
            "timezone": "Europe/Kyiv"
        }
        return self._request("/panel/stats", payload)


class SkroSync:
    def __init__(self, postback_base):
        self.postback_base = postback_base
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def push_conversion(self, click_id, revenue):
        params = urllib.parse.urlencode({
            "clickid": click_id,
            "payout": revenue,
            "txt": "api_sync"
        })
        url = f"{self.postback_base}?{params}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=self.ctx, timeout=5) as resp:
                return resp.getcode() == 200
        except Exception as e:
            # print(f"  [Sync Fail] {click_id}: {e}")
            return False


def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        print("--------------------------------")
        print("  Adw <-> Skro Tool")
        print("  Modes: create, bulk, sync")
        print("--------------------------------")
        mode = input("Select mode: ").strip().lower()

    adw = AdwClient(ADW_API_TOKEN, ADW_BASE_URL)

    # --- MODE: CREATE (Single) ---
    if mode == "create":
        print("\n--- LINK CREATION ---")
        offer_name = input("Offer ID/Name (e.g. 247_nurse): ").strip() or "247_nurse"
        buyer_tag = input("Link Name / Buyer Tag: ").strip() or "General"
        
        kw_input = input("Keywords (comma separated): ").strip()
        keywords = [k.strip() for k in kw_input.split(",") if k.strip()]
        if not keywords: keywords = ["default"]

        link_name = f"{offer_name}-{buyer_tag}"
        print(f"Creating '{link_name}' with keywords: {keywords} ...")
        
        adw_resp = adw.create_link(link_name, offer_name, keywords)
        
        if adw_resp and adw_resp.get("status") == "ok":
            url = adw_resp['data']['url']
            print(f"SUCCESS!")
            print(f"Adw URL: {url}")
            print(f"Skro Dest: {url}?sub1={{clickid}}")
        else:
            print("FAILED.")

    # --- MODE: BULK (File) ---
    elif mode == "bulk":
        filename = "bulk.csv"
        if not os.path.exists(filename):
            print(f"Error: '{filename}' not found.")
            print("Create a file 'bulk.csv' with columns: LinkName,Offer,Keywords")
            print("Example: MyLink1, 247_nurse, kw1|kw2|kw3")
            return

        print(f"\n--- BULK CREATION from {filename} ---")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                # We expect CSV or Just lines. Let's assume CSV headerless or simple structure
                # Format: LinkName, Offer, Keywords(pipe or space sep)
                print("Format expected: Name, Offer, Keywords(separated by | )")
                
                success_count = 0
                lines = f.readlines()
                print(f"Found {len(lines)} lines to process...")
                
                results = []

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#") or line.lower().startswith("name,offer"): continue
                    
                    parts = line.split(",")
                    if len(parts) < 2:
                        print(f"Skipping Invalid Line: {line}")
                        continue
                        
                    l_name = parts[0].strip()
                    l_offer = parts[1].strip()
                    l_kws_raw = parts[2].strip() if len(parts) > 2 else "default"
                    
                    # Supports | or ; for multiple keywords in CSV
                    l_kws = [k.strip() for k in l_kws_raw.replace("|", ",").replace(";", ",").split(",") if k.strip()]

                    print(f"Creating '{l_name}'... ", end="")
                    resp = adw.create_link(l_name, l_offer, l_kws)
                    
                    if resp and resp.get("status") == "ok":
                        final_url = resp['data']['url'] + "?sub1={clickid}"
                        print("OK")
                        results.append(f"{l_name},{final_url}")
                        success_count += 1
                    else:
                        print("ERROR")
                    
                    time.sleep(0.5) # throttle

                print(f"\nCompleted. Created {success_count} links.")
                
                # Save results
                with open("bulk_results.csv", "w", encoding='utf-8') as out:
                    out.write("Name,Skro_Destination_URL\n")
                    for r in results:
                        out.write(r + "\n")
                print("Results saved to 'bulk_results.csv'")

        except Exception as e:
            print(f"Error reading file: {e}")

    # --- MODE: SYNC ---
    elif mode == "sync":
        print("\n--- SYNC ADW -> SKRO ---")
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        stats_resp = adw.get_conversion_stats(today, today)
        
        if stats_resp and stats_resp.get("status") == "ok":
            data = stats_resp.get_data({}) # Correction: get("data", {})
            # Wait, get("data", {}) was correct in prev script but dict object has no get_data method.
            data = stats_resp.get("data", {})
            rows = data.get("list", [])
            print(f"Found {len(rows)} records.")
            
            syncer = SkroSync(SKRO_POSTBACK_BASE)
            count = 0
            for row in rows:
                click_id = None
                if "groups" in row and len(row["groups"]) > 0: click_id = row["groups"][0]
                elif "group" in row: click_id = row["group"]
                
                rev = row.get("revenue", 0)
                if click_id and rev > 0:
                    if syncer.push_conversion(click_id, rev): count += 1
            print(f"Synced {count} conversions.")
        else:
            print("Sync Failed or No Data.")

if __name__ == "__main__":
    main()
