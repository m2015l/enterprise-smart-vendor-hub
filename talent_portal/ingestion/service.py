from fastapi import HTTPException, status
from db.supabase_client import supabase

# Limite máximo permitido para o currículo: 5 MiB.
MAX_FILE_SIZE = 5 * 1024 * 1024


def normalize_email(email: str) -> str:
    """Remove espaços extras e padroniza o e-mail em letras minúsculas."""

    return email.strip().lower()


def normalize_cpf(cpf: str) -> str:
    """Remove a formatação do CPF e verifica se restaram 11 dígitos."""

    normalized_cpf = "".join(char for char in cpf if char.isdigit())

    if len(normalized_cpf) != 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF must have 11 digits."
        )

    return normalized_cpf


def check_duplicate_candidate(email: str, cpf: str) -> None:
    """Impede o cadastro de candidatos com e-mail ou CPF já existentes."""

    # Procura um candidato com o mesmo e-mail.
    email_match = (
        supabase
        .table("candidates")
        .select("id")
        .eq("email", email)
        .execute()
    )

    if email_match.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um candidato cadastrado com este e-mail."
        )

    # Procura um candidato com o mesmo CPF.
    cpf_match = (
        supabase
        .table("candidates")
        .select("id")
        .eq("cpf", cpf)
        .execute()
    )

    if cpf_match.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um candidato cadastrado com este CPF."
        )


def save_candidate(
    name: str,
    cpf: str,
    email: str,
    consent: bool,
    resume_text: str,
    skills: list[str],
    seniority: str | None,
    metadata: dict,
    content: bytes,
) -> dict:
    """Salva os dados do candidato, o currículo e o caminho do arquivo."""

    # Cria primeiro o registro do candidato no banco.
    response = (
        supabase
        .table("candidates")
        .insert({
            "name": name,
            "cpf": cpf,
            "email": email,
            "skills": skills,
            "seniority": seniority,
            "resume_text": resume_text,
            "consent_given": consent,
            **metadata,
        })
        .execute()
    )

    # Recupera o ID gerado para o novo candidato.
    candidate = response.data[0]
    candidate_id = candidate["id"]

    # Usa o ID como pasta para evitar colisões entre arquivos.
    resume_path = f"{candidate_id}/resume.pdf"

    try:
        # Salva o PDF no bucket privado "resumes".
        supabase.storage.from_("resumes").upload(
            path=resume_path,
            file=content,
            file_options={
                "content-type": "application/pdf",
                "upsert": "false"
            }
        )
    except Exception:
        # Se o upload falhar, remove o registro criado no banco.
        supabase.table("candidates").delete().eq(
            "id", candidate_id
        ).execute()

        raise

    try:
        # Registra no banco o caminho do currículo salvo no Storage.
        supabase.table("candidates").update({
            "resume_path": resume_path
        }).eq(
            "id", candidate_id
        ).execute()
    except Exception:
        # Se a atualização falhar, remove o arquivo e o candidato para evitar dados incompletos.
        supabase.storage.from_("resumes").remove([
            resume_path
        ])

        supabase.table("candidates").delete().eq(
            "id", candidate_id
        ).execute()

        raise

    # Retorna apenas os dados necessários para confirmar o cadastro.
    return {
        "candidate_id": candidate_id,
        "name": name,
        "email": email,
        "resume_path": resume_path,
    }


def validate_resume(content_type: str | None, content: bytes) -> None:
    """Valida tipo, tamanho e assinatura básica do arquivo de currículo."""

    # Verifica o MIME type informado no upload.
    if content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The curriculum must be a PDF file."
        )

    # Impede o envio de arquivos maiores que o limite definido.
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The curriculum must not exceed 5 MB in size."
        )

    # Confere se os bytes possuem a assinatura típica de um PDF.
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The curriculum must be a PDF file."
        )
