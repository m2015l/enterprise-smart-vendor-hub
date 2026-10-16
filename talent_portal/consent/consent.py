import os
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta


def build_candidate_metadata(consent_ip: str) -> dict:
    """Monta os metadados de consentimento e retenção do candidato."""

    # Registra o instante do consentimento em UTC.
    consent_at = datetime.now(timezone.utc)

    # Finalidade para a qual os dados pessoais serão tratados.
    consent_purpose = "Participação no banco de talentos do Enterprise Vendor Hub"

    # Texto do consentimento aceito pelo candidato.
    consent_text = (
        "Autorizo o tratamento dos meus dados pessoais para participação "
        "no banco de talentos do Enterprise Vendor Hub."
    )

    # Define retenção dos dados (padrão: 365 dias, configurável via variável de ambiente).
    retention_days = int(os.getenv("CANDIDATE_RETENTION_DAYS", "365"))
    retention_until = consent_at + timedelta(days=retention_days)

    # Retorna os campos que serão armazenados junto ao candidato.
    return {
        "origin": "talent_portal",
        "consent_text": consent_text,
        "consent_at": consent_at.isoformat(),
        "consent_purpose": consent_purpose,
        "consent_ip": consent_ip,
        "retention_until": retention_until.isoformat(),
    }


def validate_consent(consent: bool) -> None:
    """Impede o cadastro quando o candidato não dá consentimento."""

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user must consent to the data treatment."
        )
