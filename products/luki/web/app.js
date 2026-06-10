const state = {
  api: document.querySelector("#api-state"),
  collection: document.querySelector("#collection"),
  cloud: document.querySelector("#cloud"),
  audit: document.querySelector("#audit"),
  graphify: document.querySelector("#graphify"),
  answer: document.querySelector("#answer"),
  sources: document.querySelector("#sources"),
}

function setText(node, value) {
  if (node instanceof HTMLElement) {
    node.textContent = value
  }
}

function setAnswer(value, isError = false) {
  if (state.answer instanceof HTMLElement) {
    state.answer.classList.toggle("error", isError)
    state.answer.textContent = value
  }
}

async function readJson(path, options) {
  const response = await fetch(path, options)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

async function refreshStatus() {
  try {
    const [payload, graph] = await Promise.all([readJson("/api/status"), readJson("/api/graphify")])
    setText(state.api, payload.ready ? "bereit" : "geplant")
    setText(state.collection, payload.collection)
    setText(state.cloud, payload.allow_cloud ? "aktiv" : "aus")
    setText(state.audit, payload.audit_enabled ? "hash-only" : "aus")
    setText(state.graphify, graph.ready ? `${graph.nodes}/${graph.edges}` : "fehlt")
  } catch (error) {
    setText(state.api, "offline")
    setText(state.graphify, "unbekannt")
    setAnswer(error instanceof Error ? error.message : "Status nicht erreichbar", true)
  }
}

async function ask(question) {
  try {
    const payload = await readJson("/api/ask", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question }),
    })
    setAnswer(payload.answer)
    if (state.sources instanceof HTMLElement) {
      state.sources.replaceChildren(
        ...payload.sources.map((source) => {
          const item = document.createElement("li")
          item.textContent = source
          return item
        }),
      )
    }
  } catch (error) {
    setAnswer(error instanceof Error ? error.message : "Frage konnte nicht verarbeitet werden.", true)
  }
}

document.querySelector("#refresh")?.addEventListener("click", () => {
  void refreshStatus()
})

document.querySelector("#ask-form")?.addEventListener("submit", (event) => {
  event.preventDefault()
  const form = event.currentTarget
  if (!(form instanceof HTMLFormElement)) {
    return
  }
  const data = new FormData(form)
  const question = String(data.get("question") ?? "").trim()
  if (question.length === 0) {
    setAnswer("Bitte eine Frage eingeben.", true)
    return
  }
  void ask(question)
})

void refreshStatus()
