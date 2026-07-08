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
async def test_module_run_loop_renders_and_broadcasts():
    config = {
        "interval": 30,
        "county": "01",
        "max_items": 2,
        "globals": {
            "language": "sv"
        }
    }
    module = KrisinformationModule(config)
    
    # Mock data returned by Krisinformation API
    mock_api_data = [
        {
            "Identifier": "12345",
            "Headline": "Viktigt meddelande till allmänheten",
            "Preamble": "Det brinner i en industrilokal...",
            "Published": "2026-07-07T21:00:00+02:00",
            "Web": "https://krisinformation.se/nyheter/1"
        },
        {
            "Identifier": "67890",
            "Headline": "Vägar avstängda på grund av översvämning",
            "Preamble": "E6 avstängd...",
            "Published": "2026-07-07T21:15:00+02:00",
            "Web": "https://krisinformation.se/nyheter/2"
        }
    ]
    
    # Mock render_template
    module.render_template = MagicMock(return_value="<div>Mock Render</div>")
    
    # Mock broadcast_func and patch API call & sleep
    broadcast_mock = AsyncMock()
    with patch("mirrordash_krisinformation.plugin.fetch_krisinfo_api", return_value=mock_api_data) as mock_fetch:
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await module.run_loop(broadcast_mock)
                
        # Verify API fetch was called with correct parameters
        mock_fetch.assert_called_once()
        args, kwargs = mock_fetch.call_args
        assert "counties=01" in args[0]
        assert "language=sv" in args[0]
        
        # Verify render_template was called with correct context
        module.render_template.assert_called_once()
        call_kwargs = module.render_template.call_args[1]
        assert len(call_kwargs["alerts"]) == 2
        assert call_kwargs["alerts"][0]["headline"] == "Viktigt meddelande till allmänheten"
        assert call_kwargs["alerts"][0]["time"] == "21:00"
        assert call_kwargs["alerts"][1]["headline"] == "Vägar avstängda på grund av översvämning"
        assert call_kwargs["alerts"][1]["time"] == "21:15"
        
    # Verify the mock broadcast was called
    broadcast_mock.assert_called_once_with("mirrordash_krisinformation", "<div>Mock Render</div>")
