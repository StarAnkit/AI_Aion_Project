from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Artwork, MediaAsset, RightsEvidence, SourceProvider, SourceRecord
from app.domain.imports import ApprovedImportCandidate
from app.domain.rights import Cc0MediaRightsPolicy, MediaRightsCandidate


@dataclass(frozen=True, slots=True)
class ProviderRegistration:
    code: str
    name: str
    base_url: str
    rights_policy_version: str
    rights_evidence_url: str


@dataclass(slots=True)
class ImportSummary:
    created: int = 0
    unchanged: int = 0
    skipped_by_reason: Counter[str] = field(default_factory=Counter)

    @property
    def processed(self) -> int:
        return self.created + self.unchanged + sum(self.skipped_by_reason.values())


class CatalogImportService:
    """Persist only candidates that satisfy the shared policy at write time."""

    def __init__(self, policy: Cc0MediaRightsPolicy) -> None:
        self._policy = policy

    def persist_approved_candidates(
        self,
        session: Session,
        provider_registration: ProviderRegistration,
        candidates: Iterable[ApprovedImportCandidate],
    ) -> ImportSummary:
        provider: SourceProvider | None = None
        summary = ImportSummary()

        for candidate in candidates:
            decision = self._policy.evaluate(
                MediaRightsCandidate(candidate.image_url, candidate.rights_claims)
            )
            if not decision.accepted:
                summary.skipped_by_reason[f"policy_{decision.reason.value}"] += 1
                continue

            title = candidate.artwork_facts.get("title")
            if not isinstance(title, str) or not title.strip():
                summary.skipped_by_reason["missing_title"] += 1
                continue
            if not candidate.external_id or not candidate.source_url:
                summary.skipped_by_reason["missing_source_identity"] += 1
                continue

            if provider is None:
                provider = self._get_or_create_provider(session, provider_registration)

            existing = session.scalar(
                select(SourceRecord).where(
                    SourceRecord.provider_id == provider.id,
                    SourceRecord.external_id == candidate.external_id,
                )
            )
            if existing is not None:
                summary.unchanged += 1
                continue

            source_record = SourceRecord(
                provider=provider,
                external_id=candidate.external_id,
                source_url=candidate.source_url,
                raw_facts=candidate.source_facts,
                payload_sha256=_hash_facts(candidate.source_facts),
            )
            artwork = Artwork(
                source_record=source_record,
                title=title.strip(),
                creator_display=_optional_text(candidate.artwork_facts.get("creator_display")),
                date_text=_optional_text(candidate.artwork_facts.get("date_text")),
                medium=_optional_text(candidate.artwork_facts.get("medium")),
                culture=_optional_text(candidate.artwork_facts.get("culture")),
                department=_optional_text(candidate.artwork_facts.get("department")),
            )
            media_asset = MediaAsset(
                artwork=artwork,
                source_url=candidate.image_url,
                rights_status="approved",
                license_uri=candidate.rights_claims[0].license_uri,
                publication_state="published",
            )
            for claim in candidate.rights_claims:
                RightsEvidence(
                    media_asset=media_asset,
                    asserted_status=claim.status or "",
                    license_uri=claim.license_uri,
                    evidence_field=claim.evidence_field,
                    evidence_value=claim.evidence_value,
                    evidence_url=provider_registration.rights_evidence_url,
                    policy_version=provider_registration.rights_policy_version,
                )
            session.add(source_record)
            summary.created += 1

        session.flush()
        return summary

    @staticmethod
    def _get_or_create_provider(
        session: Session, registration: ProviderRegistration
    ) -> SourceProvider:
        provider = session.scalar(
            select(SourceProvider).where(SourceProvider.code == registration.code)
        )
        if provider is not None:
            provider.is_enabled = True
            return provider

        provider = SourceProvider(
            code=registration.code,
            name=registration.name,
            base_url=registration.base_url,
            rights_policy_version=registration.rights_policy_version,
            is_enabled=True,
        )
        session.add(provider)
        session.flush()
        return provider


def _hash_facts(facts: dict[str, Any]) -> str:
    import hashlib
    import json

    serialized = json.dumps(facts, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
