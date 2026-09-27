"""External-source links supplied by deployers, never a crawler or legal authority."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

_BOE_HOSTS = frozenset({"laws.boe.gov.sa", "www.boe.gov.sa"})

@dataclass(frozen=True)
class SecondaryReference:
    source_id: str
    url: str
    publisher: str = "Saudi Bureau of Experts"
    checked_at: str | None = None
    status: str = "unverified_secondary_reference"


def boe_reference(source_id: str, url: str, checked_at: str | None = None
                  ) -> SecondaryReference:
    """Validate a caller-supplied official URL; never fetch or infer currency."""
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in _BOE_HOSTS
        or parts.username or parts.password or parts.port or parts.fragment
        or not parts.path.startswith(("/BoeLaws/", "/boelaws/", "/ar/"))):
        raise ValueError("not an accepted BOE HTTPS reference URL")
    if not source_id.strip():
        raise ValueError("source ID required")
    return SecondaryReference(source_id, url, checked_at=checked_at)
