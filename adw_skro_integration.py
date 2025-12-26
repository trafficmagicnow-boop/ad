import requests
import json
import datetime

# Configuration
API_BASE_URL = "https://api.adw.net"  # Based on the provided stats/create endpoints
# Alternate: "https://api.ads.com" 
# You can switch this if one works and the other doesn't.

API_TOKEN = "0dc207a6d9701adbc8a9dd8d406ef3f4" # Provided token

# Skro Postback Setup
# Replace this with your actual Skro Postback URL found in Skro > Settings > Postback
# Usually looks like: https://s2s.skro.eu/postback?clickid={clickid}&payout={payout}
# For Adw.net, we need to map the Skro {clickid} to the parameter Adw expects (usually passed through)
# AND map the Adw macro for clickid back to Skro.
# 
# Based on Adw docs: pixel_token takes the URL. 
# Adw seems to replace {clickid} in the pixel_token with the ID we passed or its own ID.
# Best practice for Custom Sources:
# 1. We pass Skro ClickID to Adw Link:  AdwLink?sub1={clickid}  (assuming 'sub1' is the param)
# 2. Adw Postback: https://s2s.skro.eu/postback?clickid={sub1}
#
# However, the Adw docs provided use `pixel_token="https://server.com?param={clickid}"`.
# This implies Adw has an internal {clickid} macro.
SKRO_POSTBACK_TEMPLATE = "https://s2s.skro.eu/postback?clickid={clickid}&payout={revenue}"


class AdwClient:
    def __init__(self, token=API_TOKEN, base_url=API_BASE_URL):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_stats(self, date_start, date_end, group_by="time"):
        """
        Fetches statistics from Adw.net
        """
        endpoint = f"{self.base_url}/panel/stats"
        payload = {
            "date_start": date_start, # Format: DD.MM.YYYY
            "date_end": date_end,
            "groups": [group_by],
            "timezone": "Europe/Kyiv" 
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_link_for_skro(self, name, offer_name, keyword_list, skro_postback_url):
        """
        Creates a link in Adw.net configured for Skro S2S postback.
        """
        endpoint = f"{self.base_url}/panel/link_create"
        
        # Determine the pixel_token value.
        # If Skro URL is "https://s2s.skro.eu/postback?clickid={clickid}"
        # and Adw documentation says `pixel_token` is the URL to call.
        # We pass the Skro URL as the pixel_token.
        # Adw will replace macros if valid.
        
        payload = {
            "name": name,
            "offer": offer_name,
            "title": name, 
            "keywords": keyword_list,
            "postback": "s2s",
            "pixel_token": skro_postback_url, 
            "pixel_event": "lead" # Default event
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

def main():
    client = AdwClient()
    
    print("--- Adw.net <-> Skro Integration Tool ---")
    print(f"Using Token: {API_TOKEN[:6]}...")
    
    # 1. Fetch Stats Example
    today = datetime.datetime.now().strftime("%d.%m.%Y")
    print(f"\n[Stats] Fetching stats for {today}...")
    stats = client.get_stats(today, today)
    print(json.dumps(stats, indent=2))
    
    # 2. Link Creation Example
    print("\n[Link Create] Generating new link for Skro...")
    # Example details
    link_name = f"Skro_Campaign_{datetime.datetime.now().strftime('%H%M')}"
    offer = "247_nurse" # From user example
    keywords = ["test_kw1", "test_kw2"]
    
    # Setup Postback
    # Ideally, ask user for their unique Skro Postback URL
    # For demo, using a placeholder that needs to be updated
    my_skro_postback = "https://s2s.skro.eu/postback?clickid={clickid}&payout={revenue}"
    
    print(f"Creating link '{link_name}' for offer '{offer}'...")
    print(f"Configuring S2S Postback: {my_skro_postback}")
    
    new_link = client.create_link_for_skro(link_name, offer, keywords, my_skro_postback)
    print(json.dumps(new_link, indent=2))
    
    if new_link.get('status') == 'ok' and 'data' in new_link:
        url = new_link['data']['url']
        print(f"\nSUCCESS! Created Link.")
        print(f"Adw URL: {url}")
        print("\n--- INSTRUCTIONS FOR SKRO ---")
        print("1. Copy the Adw URL above.")
        print("2. Go to Skro > Campaigns > Create/Edit.")
        print("3. Paste the URL into the 'Destination URL' or 'Target URL' field.")
        print("4. IMPORTANT: Append the Skro ClickID macro to the URL so Adw receives it.")
        print(f"   Final URL for Skro: {url}?sub1={{clickid}}") 
        print("   (Note: Check Adw docs if 'sub1' is the correct param for passing click ID. If Adw uses {clickid} in postback, it often captures the first incoming param or matches cookies.)")

if __name__ == "__main__":
    main()
