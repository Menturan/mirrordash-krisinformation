import asyncio
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from mirrordash_krisinformation.plugin import URL, KrisinformationModule, when

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
    assert len(alerts) == 2 and all(a["time"] for a in alerts)
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


def test_today_shows_the_time_older_how_many_days_ago():
    translate = lambda key, default: default
    published = datetime(2026, 11, 3, 12, 33).astimezone()  # 12:33 in the mirror's time zone
    stamp = published.isoformat()
    assert when(stamp, date(2026, 11, 3), translate) == "12:33"
    assert when(stamp, date(2026, 11, 4), translate) == "Yesterday"
    assert when(stamp, date(2026, 11, 8), translate) == "5 days ago"
    assert when("", date(2026, 11, 8), translate) == ""
