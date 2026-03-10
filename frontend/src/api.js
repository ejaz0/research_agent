const API_BASE = "/api";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const bodyText = await response.text();
  const payload =
    contentType.includes("application/json") && bodyText
      ? JSON.parse(bodyText)
      : null;

  if (!response.ok) {
    const detail = payload?.detail || bodyText || `Request failed with ${response.status}`;
    throw new Error(detail);
  }

  return payload;
}

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  return parseResponse(response);
}

export function listConversations() {
  return request("/conversations", { method: "GET" });
}

export function createConversation(title = null) {
  return request("/conversations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });
}

export function getConversation(conversationId) {
  return request(`/conversations/${conversationId}`, { method: "GET" });
}

export function sendMessage(conversationId, payload) {
  return request(`/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
