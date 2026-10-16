from fastapi import APIRouter, status, Form, File, UploadFile, HTTPException, Request

from db.supabase_client import supabase
from ingestion.parser import extract_pdf_text, extract_skills, extract_seniority
from consent.consent import build_candidate_metadata, validate_consent
from ingestion.service import (
    normalize_email,
    normalize_cpf,
    check_duplicate_candidate,
    validate_resume,
    save_candidate,
)

# Agrupa os endpoints relacionados à ingestão de candidatos.
router = APIRouter()


@router.post("/candidates", status_code=status.HTTP_201_CREATED)
async def create_candidate(
    request: Request,
    name: str = Form(...),
    cpf: str = Form(...),
    email: str = Form(...),
    consent: bool = Form(...),
    resume: UploadFile = File(...)
):
    """Recebe o formulário, processa o currículo e cadastra o candidato."""

    # Garante que foi possível identificar o cliente que fez a requisição.
    if request.client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível identificar a origem da requisição."
        )

    # Registra o IP e monta os metadados ligados a consentimento e retenção.
    consent_ip = request.client.host
    metadata = build_candidate_metadata(consent_ip)

    # Padroniza os campos usados para identificação e deduplicação.
    email = normalize_email(email)
    cpf = normalize_cpf(cpf)

    # Bloqueia CPF ou e-mail já cadastrados.
    check_duplicate_candidate(email, cpf)

    # Exige o consentimento para tratamento dos dados.
    validate_consent(consent)

    # Lê o conteúdo enviado no campo de currículo.
    content = await resume.read()

    # Valida se o arquivo recebido pode ser aceito como currículo PDF.
    validate_resume(resume.content_type, content)

    # Extrai texto e alguns campos estruturados do currículo.
    resume_text = extract_pdf_text(content)
    skills = extract_skills(resume_text)
    seniority = extract_seniority(resume_text)

    # Persiste os dados no banco e o arquivo no Supabase Storage.
    result = save_candidate(
        name=name,
        cpf=cpf,
        email=email,
        consent=consent,
        resume_text=resume_text,
        skills=skills,
        seniority=seniority,
        metadata=metadata,
        content=content,
    )

    return result


@router.get("/candidates")
def list_cadidates():
    """Lista campos básicos dos candidatos cadastrados."""

    # Consulta somente os campos necessários para validar os registros salvos.
    response = (
        supabase
        .table("candidates")
        .select(
            "id, name, email, skills, seniority, origin, created_at"
        )
        .execute()
    )

    return response.data
