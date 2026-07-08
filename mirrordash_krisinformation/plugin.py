import asyncio
import logging
import json
import urllib.request
import urllib.parse
from datetime import datetime

logger = logging.getLogger("mirrordash.modules.mirrordash_krisinformation")

def fetch_krisinfo_api(url: str) -> list[dict]:
    """Synchronous network fetch helper to run inside asyncio.to_thread."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MirrorDash/0.1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = response.read()
                return json.loads(data.decode("utf-8"))
            else:
                logger.error(f"Krisinformation API returned status {response.status}")
    except Exception as e:
        logger.error(f"Error calling Krisinformation API: {e}")
    return []

class KrisinformationModule:
    # Prevent pytest from trying to collect this class as a test case/suite
    __test__ = False

    def __init__(self, config):
        self.config = config
        self.name = "mirrordash_krisinformation"
        self.interval = config.get("interval", 300)
        
        # Injected directories
        self.data_dir = config.get("data_dir")
        self.cache_dir = config.get("cache_dir")
        self.translations = config.get("translations", {})
        
        # Read from global configuration
        global_cfg = config.get("globals", {})
        self.language = config.get("language", global_cfg.get("language", "sv"))
        self.timezone = global_cfg.get("timezone", "Europe/Stockholm")
        
        # Custom module configurations
        self.county = config.get("county", "")
        self.max_items = config.get("max_items", 3)
        self.show_preamble = config.get("show_preamble", True)
        self.show_header = config.get("show_header", True)
        
        logger.info(f"Initializing {self.name} module for county '{self.county}'")

    def translate(self, key: str, default: str = None) -> str:
        if not self.translations:
            return default if default is not None else key
        return self.translations.get(key, default if default is not None else key)

    async def run_loop(self, broadcast_func):
        logger.info(f"Starting {self.name} run loop")
        while True:
            try:
                # Build API URL
                # Krisinformation expects query parameters.
                # v3/news?format=json&language={lang}
                params = {
                    "format": "json",
                    "language": self.language
                }
                
                if self.county:
                    params["counties"] = self.county

                query_string = urllib.parse.urlencode(params)
                url = f"https://api.krisinformation.se/v3/news?{query_string}"

                logger.debug(f"Fetching Krisinformation alerts from: {url}")
                raw_alerts = await asyncio.to_thread(fetch_krisinfo_api, url)
                
                alerts = []
                for item in raw_alerts[:self.max_items]:
                    published_str = item.get("Published", "")
                    time_display = ""
                    if published_str:
                        try:
                            # Published is e.g. "2026-07-01T08:01:38+02:00"
                            # Parse it to a localized format.
                            dt = datetime.fromisoformat(published_str)
                            time_display = dt.strftime("%H:%M")
                        except Exception:
                            time_display = ""

                    alerts.append({
                        "id": item.get("Identifier"),
                        "headline": item.get("Headline", ""),
                        "preamble": item.get("Preamble", ""),
                        "time": time_display,
                        "web_url": item.get("Web", "")
                    })

                html = self.render_template(
                    "widget.html",
                    alerts=alerts,
                    show_preamble=self.show_preamble,
                    show_header=self.show_header,
                    error=self.translate("error_fetching", "Error loading crisis alerts") if not raw_alerts and raw_alerts is None else None
                )
                
                await broadcast_func(self.name, html)
                
            except asyncio.CancelledError:
                logger.info(f"{self.name} module stopped.")
                raise
            except Exception as e:
                logger.error(f"Error in module {self.name} run_loop: {e}")
                
            await asyncio.sleep(self.interval)
