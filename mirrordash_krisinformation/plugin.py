import asyncio
import logging
from datetime import datetime

logger = logging.getLogger("mirrordash.modules.mirrordash_krisinformation")

URL = "https://api.krisinformation.se/v3/news"


def parse(items, max_items: int) -> list[dict]:
    """The API's news items -> what the template shows (the API names its fields in camelCase)."""
    alerts = []
    for item in (items if isinstance(items, list) else [])[:max_items]:
        try:
            time = datetime.fromisoformat(item.get("published", "")).strftime("%H:%M")
        except ValueError:
            time = ""
        alerts.append({
            "id": item.get("identifier"),
            "headline": item.get("headline", ""),
            "preamble": item.get("preamble", ""),
            "time": time,
            "web_url": item.get("web", ""),
        })
    return alerts


class KrisinformationModule:
    # Keeps pytest from collecting this class as a test
    __test__ = False

    def __init__(self, config):
        # The mirror adds self.render_template, self.translate and self.fetch_json after __init__.
        self.config = config
        self.name = "mirrordash_krisinformation"
        self.interval = config.get("interval", 300)
        global_cfg = config.get("globals", {})
        self.language = config.get("language", global_cfg.get("language", "sv"))
        self.county = config.get("county", "")
        self.max_items = config.get("max_items", 3)
        self.show_preamble = config.get("show_preamble", True)

    async def render(self) -> str:
        params = {"format": "json", "language": self.language}
        if self.county:
            params["counties"] = self.county
        # On a failure, data is the last good answer (also after a restart)
        data, error = await self.fetch_json(URL, params=params)
        return self.render_template(
            "widget.html",
            alerts=parse(data, self.max_items),
            show_preamble=self.show_preamble,
            error=self.translate("error_fetching", "Error loading crisis alerts") if data is None else None,
        )

    async def run_loop(self, broadcast_func):
        while True:
            try:
                await broadcast_func(self.name, await self.render())
            except asyncio.CancelledError:
                raise  # the mirror is stopping this module: let it
            except Exception as e:
                logger.error(f"{self.name}: {e}", exc_info=True)
            await asyncio.sleep(self.interval)
