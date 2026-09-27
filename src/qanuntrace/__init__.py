"""QanunTrace: source-grounded legal evidence building blocks."""
from .access import AuthorizedStore
from .core import Generator, LegalStore, Pipeline, reference_key, search_key, verify
from .gateway import TransferDecision, prepare_remote_transfer
from .health import HealthReport, health_check
from .legal_reference import LegislativeReference, parse_legislative_reference
from .model_bridge import FunctionModel, ProposalBridge, TextModel
from .privacy import RedactedText, SensitiveSpan, detect, redact
from .secondary import SecondaryReference, boe_reference
from .temporal import VersionView, version_view
from .types import Answer, AuditEvent, EvidenceProposal, Finding, LegalRecord, Query

__all__ = [
    "Answer", "AuditEvent", "AuthorizedStore", "EvidenceProposal", "Finding",
    "FunctionModel", "Generator", "HealthReport", "LegalRecord", "LegalStore",
    "LegislativeReference", "Pipeline", "ProposalBridge", "Query", "RedactedText",
    "SecondaryReference", "SensitiveSpan", "TextModel", "TransferDecision", "VersionView",
    "boe_reference", "detect", "health_check", "parse_legislative_reference",
    "prepare_remote_transfer", "redact", "reference_key", "search_key", "verify",
    "version_view",
]
