const apiStatus = document.querySelector("#api-status");

async function checkApiHealth() {
  try {
    const response = await fetch("/health");

    if (!response.ok) {
      throw new Error(`API respondeu com status ${response.status}`);
    }

    const data = await response.json();
    apiStatus.textContent = data.status === "ok" ? "API online" : "API indisponível";
    apiStatus.classList.toggle("status-online", data.status === "ok");
  } catch (error) {
    apiStatus.textContent = "API indisponível";
    apiStatus.title = error.message;
  }
}

checkApiHealth();
