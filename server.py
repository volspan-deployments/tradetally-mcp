from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("TradeTally")

BASE_URL = os.environ.get("TRADETALLY_BASE_URL", "http://localhost:3000") + "/api/v1"
JWT_SECRET = os.environ.get("JWT_SECRET", "")


def get_headers() -> dict:
    """Build authorization headers using the JWT secret as bearer token."""
    return {
        "Authorization": f"Bearer {JWT_SECRET}",
        "Content-Type": "application/json",
    }


@mcp.tool()
async def get_trades(
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    broker: Optional[str] = None,
    trade_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> dict:
    """Retrieve a list of trades from the trading journal. Use this when the user wants to view, filter, or search their trade history. Supports filtering by date range, symbol, broker, trade type (options/futures/stocks), and status."""
    params = {"page": page, "limit": limit}
    if symbol:
        params["symbol"] = symbol
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if broker:
        params["broker"] = broker
    if trade_type:
        params["trade_type"] = trade_type

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/trades",
            headers=get_headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    metric: Optional[str] = None,
    broker: Optional[str] = None,
    trade_type: Optional[str] = None,
) -> dict:
    """Retrieve performance analytics and statistics for the user's trading activity. Use this when the user wants to understand their trading performance, win rate, P&L by day/week/sector, hold times, or behavioral patterns like revenge trading. Returns aggregated metrics and chart data."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if metric:
        params["metric"] = metric
    if broker:
        params["broker"] = broker
    if trade_type:
        params["trade_type"] = trade_type

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/analytics",
            headers=get_headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_ai_insights(
    question: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Request AI-powered trading analysis and personalized recommendations using Google Gemini. Use this when the user wants actionable insights, pattern detection, behavioral feedback, or personalized coaching based on their trading history."""
    payload = {}
    if question:
        payload["question"] = question
    if start_date:
        payload["start_date"] = start_date
    if end_date:
        payload["end_date"] = end_date

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/analytics/ai-insights",
            headers=get_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def import_trades(
    broker: str,
    file_content: str,
    account_id: Optional[str] = None,
) -> dict:
    """Import trades from a broker CSV file into the trading journal. Use this when the user wants to upload a trade export file from a supported broker. Handles CSV parsing and field mapping for Lightspeed, Charles Schwab, ThinkorSwim, IBKR, E*TRADE, and ProjectX."""
    payload: dict = {
        "broker": broker,
        "file_content": file_content,
    }
    if account_id:
        payload["account_id"] = account_id

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/trades/import",
            headers=get_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def manage_api_keys(
    action: str,
    key_name: Optional[str] = None,
    key_id: Optional[str] = None,
) -> dict:
    """Create, list, or revoke API keys for programmatic access to TradeTally. Use this when the user wants to generate a new API key for integrations, view existing keys, or delete a key that is no longer needed."""
    if action not in ("create", "list", "revoke"):
        return {"error": "action must be one of: create, list, revoke"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        if action == "list":
            response = await client.get(
                f"{BASE_URL}/api-keys",
                headers=get_headers(),
            )
            response.raise_for_status()
            return response.json()

        elif action == "create":
            if not key_name:
                return {"error": "key_name is required when action is create"}
            payload = {"name": key_name}
            response = await client.post(
                f"{BASE_URL}/api-keys",
                headers=get_headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

        else:  # revoke
            if not key_id:
                return {"error": "key_id is required when action is revoke"}
            response = await client.delete(
                f"{BASE_URL}/api-keys/{key_id}",
                headers=get_headers(),
            )
            response.raise_for_status()
            return response.json() if response.content else {"message": "API key revoked successfully"}


@mcp.tool()
async def get_year_wrapped(year: int) -> dict:
    """Retrieve a year-in-review summary of the user's trading activity, similar to Spotify Wrapped. Use this when the user wants a highlight reel of their trading stats, best/worst trades, streaks, and behavioral patterns for a given year."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/analytics/wrapped/{year}",
            headers=get_headers(),
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def lookup_cusip(
    cusip: Optional[str] = None,
    symbol: Optional[str] = None,
) -> dict:
    """Look up security information using a CUSIP identifier, or resolve a CUSIP to its ticker symbol. Use this when processing trades that use CUSIP codes instead of ticker symbols, or when the user needs to identify an instrument by its CUSIP."""
    if not cusip and not symbol:
        return {"error": "At least one of cusip or symbol must be provided"}

    params = {}
    if cusip:
        params["cusip"] = cusip
    if symbol:
        params["symbol"] = symbol

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/cusip/lookup",
            headers=get_headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def admin_get_server_status(include_metrics: bool = True) -> dict:
    """Retrieve server health, instance configuration, and admin-level platform statistics. Use this when an admin user needs to check system status, active user counts, registration mode, or overall platform health metrics."""
    params = {"include_metrics": str(include_metrics).lower()}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/admin/status",
            headers=get_headers(),
            params=params,
        )
        if response.status_code == 404:
            # Fall back to public server info endpoints
            health_response = await client.get(
                f"{BASE_URL}/server/health",
                headers=get_headers(),
            )
            info_response = await client.get(
                f"{BASE_URL}/server/info",
                headers=get_headers(),
            )
            result = {}
            if health_response.status_code == 200:
                result["health"] = health_response.json()
            if info_response.status_code == 200:
                result["info"] = info_response.json()
            return result
        response.raise_for_status()
        return response.json()




_SERVER_SLUG = "tradetally"

def _track(tool_name: str, ua: str = ""):
    try:
        import urllib.request, json as _json
        data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
        req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

mcp_app = mcp.http_app(transport="streamable-http")

class _FixAcceptHeader:
    """Ensure Accept header includes both types FastMCP requires."""
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()
            if "text/event-stream" not in accept:
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", b"application/json, text/event-stream"))
                scope = dict(scope, headers=new_headers)
        await self.app(scope, receive, send)

app = _FixAcceptHeader(Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", mcp_app),
    ],
    lifespan=mcp_app.lifespan,
))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
