"""Opt-in HTTP transport for approved government API contracts, no assumed endpoints."""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit


@dataclass(frozen=True)
class GovernmentAPI:
    name: str
    base_url: str
    allowed_host: str
    auth_header: str | None = None
    auth_value: str | None = None

    def __post_init__(self) -> None:
        parsed = urlsplit(self.base_url)
        if (parsed.scheme != "https" or parsed.hostname != self.allowed_host
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.port or not self.allowed_host):
            raise ValueError("fixed HTTPS government API host required")
        if (self.auth_header is None) != (self.auth_value is None):
            raise ValueError("authentication header and value must be supplied together")
        if self.auth_header and (not self.auth_header.isascii() or not self.auth_header.replace('-', '').isalnum()):
            raise ValueError("invalid authentication header")

@dataclass(frozen=True)
class APIResponse:
    source: str
    endpoint: str
    data: object
    needs_review: bool = True


def approved_get(api: GovernmentAPI, endpoint: str,
                 fetch: Callable[[str, Mapping[str, str]], bytes],
                 *, approved: bool = False, max_bytes: int = 2_000_000) -> APIResponse:
    """Caller owns contract, keys, licensing, rate limits and access approval.

    `fetch` must enforce TLS, timeouts and no redirects; no network client is bundled.
    Response text is untrusted and never promoted to a verified LegalRecord here.
    """
    if not approved:
        raise PermissionError("deployer API approval and data rights required")
    if (not endpoint.startswith('/') or endpoint.startswith('//')
        or '\\' in endpoint or '..' in endpoint.split('/')):
        raise ValueError("endpoint must be an absolute path on the approved host")
    url = urljoin(api.base_url.rstrip('/') + '/', endpoint.lstrip('/'))
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != api.allowed_host or parsed.fragment:
        raise ValueError("endpoint leaves approved host")
    headers = {'Accept': 'application/json'}
    if api.auth_header and api.auth_value:
        headers[api.auth_header] = api.auth_value
    raw = fetch(url, headers)
    if len(raw) > max_bytes:
        raise ValueError("API response size limit")
    return APIResponse(api.name, url, json.loads(raw.decode('utf-8', 'strict')))

# These are catalog origins, not asserted data endpoints or proof of access.
NAJIZ_CATALOG = "https://developers.najiz.sa/en/api-catalog"
MOJ_OPEN_DATA_POLICY = "https://www.moj.gov.sa/ar/OpenData/Pages/OpenDataPolicy.aspx"
SBA_LIBRARY_LANDING = "https://library-api.sba.gov.sa/"
