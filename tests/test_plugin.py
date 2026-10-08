import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mirrordash_krisinformation.plugin import URL, KrisinformationModule

# The API's answer, as it looks today (camelCase field names)
API_DATA = [
    {"identifier": "12345", "headline": "Viktigt meddelande till allmänheten", "preamble": "Det brinner i en industrilokal...",
     "published": "2026-07-07T21:00:00+02:00", "web": "https://krisinformation.se/nyheter/1"},
    {"identifier": "67890", "headline": "Vägar avstängda på grund av översvämning", "preamble": "E6 avstängd...",
     "published": "2026-07-07T21:15:00+02:00", "web": "https://krisinformation.se/nyheter/2"},
    {"identifier": "3", "headline": "Tredje", "preamble": "", "published": "", "web": ""},
]


def module(answer, **config):
    m = KrisinformationModule({"globals": {"language": "sv"}, **config})
    m.fetch_json = AsyncMock(return_value=answer)
    m.render_template = MagicMock(return_value="<div>Mock Render</div>")
    m.translate = lambda key, default: default
    return m


def test_module_initialization():
    m = KrisinformationModule({"interval": 15, "globals": {"language": "en"}})
    assert m.name == "mirrordash_krisinformation"
    assert m.interval == 15
    assert m.language == "en"


def test_alerts_from_the_api():
    m = module((API_DATA, None), county="01", max_items=2)
    asyncio.run(m.render())
    m.fetch_json.assert_awaited_once_with(URL, params={"format": "json", "language": "sv", "counties": "01"})
    alerts = m.render_template.call_args.kwargs["alerts"]
    assert [a["headline"] for a in alerts] == ["Viktigt meddelande till allmänheten", "Vägar avstängda på grund av översvämning"]
    assert [a["time"] for a in alerts] == ["21:00", "21:15"]
    assert m.render_template.call_args.kwargs["error"] is None


def test_last_answer_is_shown_when_offline_and_error_without_one():
    m = module((API_DATA, "offline"))
    asyncio.run(m.render())
    assert len(m.render_template.call_args.kwargs["alerts"]) == 3
    assert m.render_template.call_args.kwargs["error"] is None

    m = module((None, "offline"))
    asyncio.run(m.render())
    assert m.render_template.call_args.kwargs["alerts"] == []
    assert m.render_template.call_args.kwargs["error"] == "Error loading crisis alerts"


@pytest.mark.asyncio
async def test_run_loop_broadcasts_and_stops_when_cancelled():
    m = module(([], None))
    broadcast = AsyncMock(side_effect=asyncio.CancelledError)
    with pytest.raises(asyncio.CancelledError):
        await m.run_loop(broadcast)
    broadcast.assert_awaited_once_with("mirrordash_krisinformation", "<div>Mock Render</div>")
