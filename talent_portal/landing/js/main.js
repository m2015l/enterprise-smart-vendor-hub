const form = document.getElementById("candidate-form");
const submitBtn = document.getElementById("submit-btn");
const message = document.getElementById("form-message");

function showMessage(text, type) {
  message.textContent = text;
  message.className = `form-message visible ${type}`;
}

function hideMessage() {
  message.className = "form-message";
}

async function submitCandidate(formData) {
  const response = await fetch(`${window.API_BASE_URL}/candidates`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data && data.detail ? data.detail : "Não foi possível enviar sua candidatura.";
    throw new Error(detail);
  }

  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  const formData = new FormData();
  formData.append("name", form.name.value.trim());
  formData.append("email", form.email.value.trim());
  formData.append("cpf", form.cpf.value.trim());
  formData.append("consent", form.consent.checked ? "true" : "false");
  formData.append("resume", form.resume.files[0]);

  submitBtn.disabled = true;
  submitBtn.textContent = "Enviando...";

  try {
    await submitCandidate(formData);
    showMessage("Candidatura enviada com sucesso! Em breve entraremos em contato.", "success");
    form.reset();
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Enviar candidatura";
  }
});
