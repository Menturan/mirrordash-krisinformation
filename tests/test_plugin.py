import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from mirrordash_krisinformation.plugin import KrisinformationModule

def test_module_initialization():
    config = {
        "interval": 15,
        "globals": {
            "language": "en",
            "timezone": "Europe/Stockholm"
        }
    }
    module = KrisinformationModule(config)
    assert module.name == "mirrordash_krisinformation"
    assert module.interval == 15

@pytest.mark.asyncio
async def test_module_run_loop():
    config = {
        "interval": 30,
        "globals": {
            "language": "en"
        }
    }
    module = KrisinformationModule(config)
    
    # Mock render_template
    module.render_template = MagicMock(return_value="<div>Mock Render</div>")
    
    # Mock broadcast_func and patch asyncio.sleep to break the loop
    broadcast_mock = AsyncMock()
    with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await module.run_loop(broadcast_mock)
            
    # Verify the mock broadcast was called
    broadcast_mock.assert_called_once_with("mirrordash_krisinformation", "<div>Mock Render</div>")
