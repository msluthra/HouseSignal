"""RentCast API client with strict cache-first access and daily request caps."""

from __future__ import annotations

from typing import Any

import httpx

from config.settings import settings
from src.cache.api_cache import ApiCache
from src.security.secrets import require_secret


class RentCastClient:
    """Backend-only RentCast client.

    The client never exposes or logs the API key. It checks the local cache before
    making a network call and enforces a configurable daily miss limit.
    """

    provider = "rentcast"

    def __init__(self, cache: ApiCache | None = None) -> None:
        self.cache = cache or ApiCache()
        self.base_url = settings.rentcast_base_url.rstrip("/")
        self.daily_limit = settings.rentcast_daily_limit
        self.cache_ttl_hours = settings.rentcast_cache_ttl_hours

    def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        cached = self.cache.get(self.provider, endpoint, params)
        if cached.hit and cached.payload is not None:
            self.cache.log_usage(self.provider, endpoint, cached.cache_key, "hit")
            return cached.payload

        self.cache.ensure_daily_limit(self.provider, endpoint, self.daily_limit, cached.cache_key)
        api_key = require_secret(settings.rentcast_api_key, "RENTCAST_API_KEY")
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"X-Api-Key": api_key, "accept": "application/json"}

        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError:
            self.cache.log_usage(self.provider, endpoint, cached.cache_key, "error")
            raise

        self.cache.set(self.provider, endpoint, params, payload, self.cache_ttl_hours)
        self.cache.log_usage(self.provider, endpoint, cached.cache_key, "miss")
        return payload

    def property_details(self, address: str) -> dict[str, Any]:
        """Fetch details for one property address."""
        return self._get("properties", {"address": address})

    def rent_estimate(self, address: str, bedrooms: float | None = None, bathrooms: float | None = None) -> dict[str, Any]:
        """Fetch a rent estimate for one property address."""
        params: dict[str, Any] = {"address": address}
        if bedrooms is not None:
            params["bedrooms"] = bedrooms
        if bathrooms is not None:
            params["bathrooms"] = bathrooms
        return self._get("avm/rent/long-term", params)

    def sale_listings(self, city: str, state: str = "CA", limit: int = 25) -> dict[str, Any]:
        """Fetch sale listings for a city with a low default limit."""
        return self._get("listings/sale", {"city": city, "state": state, "limit": min(limit, 25)})
