import re
from io import BytesIO
from pypdf import PdfReader

# Títulos que podem identificar a seção de competências do currículo.
SKILLS_HEADINGS = {
    "competências",
    "competencias",
    "skills",
    "technical skills",
    "habilidades",
    "tecnologias",
    "technologies",
}

# Títulos usados para identificar quando uma seção do currículo termina e outra começa.
SECTION_HEADINGS = SKILLS_HEADINGS | {
    "experiência",
    "experiencia",
    "experience",
    "experiência profissional",
    "experiencia profissional",
    "professional experience",
    "formação",
    "formacao",
    "education",
    "idiomas",
    "languages",
    "projetos",
    "projects",
    "certificações",
    "certificacoes",
    "certifications",
}


def extract_pdf_text(content: bytes) -> str:
    """Extrai e junta o texto das páginas de um PDF."""

    # Converte os bytes recebidos em um arquivo em memória.
    pdf_file = BytesIO(content)
    reader = PdfReader(pdf_file)

    pages_text = []

    # Extrai o texto de cada página que possuir conteúdo textual.
    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text)

    return "\n".join(pages_text)


def normalize_heading(text: str) -> str:
    """Normaliza um possível título de seção para facilitar comparações."""

    return text.strip().lower().rstrip(":")


def extract_skills_section(text: str) -> str | None:
    """Extrai apenas o conteúdo da seção de competências do currículo."""

    # Remove linhas vazias e espaços extras.
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    collecting = False
    skill_lines = []

    for line in lines:
        normalized = normalize_heading(line)

        # Começa a coletar quando encontra um título de competências.
        if normalized in SKILLS_HEADINGS:
            collecting = True
            continue

        # Para quando encontra o início de outra seção.
        if collecting and normalized in SECTION_HEADINGS:
            break

        if collecting:
            skill_lines.append(line)

    if not skill_lines:
        return None

    return "\n".join(skill_lines)


def extract_skills(text: str) -> list[str]:
    """Transforma a seção de competências em uma lista de skills."""

    section = extract_skills_section(text)

    if section is None:
        return []

    # Divide as competências por separadores comuns em currículos.
    skills = re.split(r"[\n,;|•]+", section)

    # Remove espaços e itens vazios.
    return [
        skill.strip()
        for skill in skills
        if skill.strip()
    ]


def extract_seniority(text: str) -> str | None:
    """Busca uma indicação explícita de senioridade no currículo."""

    text_lower = text.lower()

    # A ordem prioriza a maior senioridade caso mais de uma apareça no texto.
    if "sênior" in text_lower or "senior" in text_lower:
        return "senior"

    if "pleno" in text_lower:
        return "pleno"

    if "júnior" in text_lower or "junior" in text_lower:
        return "junior"

    # Retorna None quando não encontra indicação explícita.
    return None
