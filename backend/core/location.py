import ipaddress
from typing import Optional

import httpx
from fastapi import Request


async def locate_request(request: Request) -> Optional[dict]:
    """Resolve a coarse public-IP location without retaining the IP address."""
    forwarded = request.headers.get("x-forwarded-for", "")
    ip_text = forwarded.split(",", 1)[0].strip() if forwarded else ""
    if not ip_text and request.client:
        ip_text = request.client.host

    try:
        ip = ipaddress.ip_address(ip_text)
        if not ip.is_global:
            return None
    except ValueError:
        return None

    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.get(f"https://ipapi.co/{ip}/json/")
            response.raise_for_status()
            data = response.json()
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            return None
        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "city": data.get("city"),
            "country": data.get("country_name"),
        }
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return None
