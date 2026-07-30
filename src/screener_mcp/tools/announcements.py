"""
Company announcements — fetch and filter NSE corporate disclosures.
"""

import logging
from datetime import datetime

from ..core.nse_client import get_nse_client

logger = logging.getLogger(__name__)

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "results": ["financial results", "quarterly results", "annual results", "q1", "q2", "q3", "q4", "half year"],
    "board_meeting": ["board meeting", "board of directors"],
    "dividend": ["dividend"],
    "insider_trading": ["insider trading", "promoter", "bulk deal", "block deal", "sast"],
    "agm": ["agm", "annual general meeting", "egm", "extraordinary general meeting"],
    "acquisition": ["acquisition", "merger", "demerger", "amalgamation", "takeover"],
    "buyback": ["buyback", "buy-back", "share repurchase"],
    "fund_raise": ["rights issue", "ipo", "fpo", "ncd", "debenture", "preferential allotment"],
}


def _categorize(headline: str, subject: str) -> str:
    text = (headline + " " + subject).lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return "general"


def _within_days(date_str: str, days: int) -> bool:
    """Return True if date_str falls within the last N days."""
    for fmt in ["%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%d %b %Y"]:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return (datetime.now() - dt).days <= days
        except ValueError:
            continue
    return True  # include if unparseable


async def get_company_announcements(
    symbol: str,
    category: str = "all",
    days: int = 30,
) -> str:
    """
    Fetch recent company announcements from NSE.

    symbol: NSE trading symbol (e.g., "TCS", "RELIANCE")
    category: "all" | "results" | "board_meeting" | "dividend" | "insider_trading"
              | "agm" | "acquisition" | "buyback" | "fund_raise"
    days: look back this many days (default 30, max 365)
    """
    valid_categories = {"all"} | set(_CATEGORY_KEYWORDS.keys())
    if category not in valid_categories:
        return (
            f"**Invalid category '{category}'.**\n\n"
            f"Valid options: {', '.join(sorted(valid_categories))}"
        )

    nse = await get_nse_client()
    items = await nse.get_announcements(symbol)

    if not items:
        return (
            f"**No announcements found for {symbol.upper()}.**\n\n"
            f"Possible reasons:\n"
            f"  - Symbol is incorrect — use `search_company('{symbol}')` to verify\n"
            f"  - NSE API is temporarily unavailable\n"
            f"  - Company has no recent announcements\n"
        )

    filtered = [a for a in items if _within_days(a.get("date", ""), days)]

    if category != "all":
        filtered = [
            a for a in filtered
            if _categorize(a.get("headline", ""), a.get("category", "")) == category
        ]

    if not filtered:
        return (
            f"**No {category} announcements found for {symbol.upper()} in the last {days} days.**\n\n"
            f"Total announcements (all categories, all dates): {len(items)}\n"
            f"Try: `category='all'` or increase `days`."
        )

    lines = [
        f"# Company Announcements — {symbol.upper()}",
        f"Filter: {category} | Last {days} days | {len(filtered)} found",
        "",
    ]

    shown = filtered[:50]
    for ann in shown:
        date = ann.get("date", "Unknown date")
        headline = (ann.get("headline") or ann.get("category") or "No description")[:120]
        cat = _categorize(ann.get("headline", ""), ann.get("category", ""))
        url = ann.get("url", "")

        lines.append(f"[{date}] [{cat.upper()}]")
        lines.append(f"  {headline}")
        if url:
            lines.append(f"  PDF: {url}")
        lines.append("")

    if len(filtered) > 50:
        lines.append(f"... and {len(filtered) - 50} more. Narrow with `category` or reduce `days`.")

    return "\n".join(lines)
