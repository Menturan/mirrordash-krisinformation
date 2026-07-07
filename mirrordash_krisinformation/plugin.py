import asyncio
import logging
import os
from datetime import datetime

logger = logging.getLogger("mirrordash.modules.mirrordash_krisinformation")

class KrisinformationModule:
    # Prevent pytest from trying to collect this class as a test case/suite
    __test__ = False

    def __init__(self, config):
        self.config = config
        self.name = "mirrordash_krisinformation"
        self.interval = config.get("interval", 30)
        
        # Writable data directory (persistent, backed up) and cache directory (transient, excluded from backups)
        self.data_dir = config.get("data_dir")
        self.cache_dir = config.get("cache_dir")
        
        # Translation dictionary containing strings merged from translations/*.json files
        self.translations = config.get("translations", {})
        
        # Event Bus for inter-module communication (pub/sub)
        self.event_bus = config.get("event_bus")
        
        logger.info(f"Initializing {self.name} module")

    async def run_loop(self, broadcast_func):
        """
        The main lifecycle loop. Fetch data, format HTML, and broadcast.
        If you want to use a synchronous blocking loop instead, simply remove 'async'
        from the signature (def run_loop) and call broadcast_func synchronously.
        """
        logger.info(f"Starting {self.name} run loop")
        while True:
            try:
                # 1. Fetch or compute your module's data here (e.g. caches, REST APIs)
                current_time = datetime.now().strftime("%H:%M:%S")
                
                # 2. Render dynamic HTML using Jinja2 template
                # (self.render_template is automatically injected by the core module loader
                # if your module package contains a 'templates' directory)
                html = self.render_template(
                    "widget.html",
                    current_time=current_time
                )
                
                # 3. Broadcast HTML update to the UI (no per-tick log to prevent spam)
                await broadcast_func(self.name, html)
                
            except asyncio.CancelledError:
                logger.info(f"{self.name} module stopped.")
                raise
            except Exception as e:
                logger.error(f"Error in module {self.name} run_loop: {e}")
                
            await asyncio.sleep(self.interval)
