/* ===========================
   NOVA — AI Voice Assistant
   script.js (FULLY FIXED)
   
   FIXES:
   ✅ localStorage key matches login.html (nova_token)
   ✅ Session management & chat history
   ✅ User email display
=========================== */

// Auto-detect backend URL based on environment
const BACKEND_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8000"
  : "https://nova-ai-voice-assistant.onrender.com";

const TOKEN = localStorage.getItem("nova_token");
const USER_EMAIL = localStorage.getItem("nova_email");

if (!TOKEN) {
  window.location.href = "login.html";
}

// DOM Elements
const chatBox = document.getElementById("chat");
const micBtn = document.getElementById("micBtn");
const statusPill = document.getElementById("statusPill");
const statusText = document.getElementById("statusText");
const textInput = document.getElementById("textInput");
const welcomeScreen = document.getElementById("welcomeScreen");
const toast = document.getElementById("toast");
const userEmail = document.getElementById("userEmail");
const userAvatar = document.getElementById("userAvatar");
const sessionsList = document.getElementById("sessionsList");
const headerTitle = document.getElementById("headerTitle");
const sidebar = document.getElementById("sidebar");

// State
let currentSessionId = null;
let conversationHistory = [];
let isListening = false;

// Display user email
if (userEmail && USER_EMAIL) {
  userEmail.textContent = USER_EMAIL;
  userAvatar.textContent = USER_EMAIL[0].toUpperCase();
}

// ─── SPEECH RECOGNITION ───
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.continuous = false;

  recognition.onstart = () => {
    isListening = true;
    setStatus("listening", "Listening…");
    micBtn.classList.add("listening");
  };

  recognition.onresult = (event) => {
    const userText = event.results[0][0].transcript.trim();
    if (userText) handleUserMessage(userText);
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove("listening");
    if (statusText.textContent === "Listening…") {
      setStatus("", "Ready");
    }
  };

  recognition.onerror = (event) => {
    isListening = false;
    micBtn.classList.remove("listening");
    const errorMessages = {
      "no-speech": "⚠️ No speech detected",
      "not-allowed": "🚫 Microphone denied",
      "audio-capture": "🎤 No microphone found",
      "network": "🌐 Network error",
    };
    if (errorMessages[event.error]) showToast(errorMessages[event.error]);
  };
} else {
  micBtn.style.display = "none";
}

// ─── MIC & INPUT ───
function startListening() {
  if (!recognition) return;
  if (isListening) {
    recognition.stop();
  } else {
    try {
      recognition.start();
    } catch (e) {
      if (e.message.includes("already started")) {
        recognition.stop();
        setTimeout(() => recognition.start(), 300);
      }
    }
  }
}

function handleKey(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendText();
  }
}

function sendText() {
  const text = textInput.value.trim();
  if (text) {
    textInput.value = "";
    autoResize(textInput);
    handleUserMessage(text);
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

// ─── MAIN CHAT HANDLER ───
async function handleUserMessage(text) {
  if (welcomeScreen) welcomeScreen.style.display = "none";

  addMessage(text, "user");
  conversationHistory.push({ role: "user", content: text });

  setStatus("thinking", "Thinking…");
  const typingEl = addTypingIndicator();

  try {
    const result = await fetchAIResponse(text);
    console.log("Backend result:", result);
    typingEl.remove();
    setStatus("", "Ready");

    addMessage(result.reply, "bot");
    conversationHistory.push({ role: "assistant", content: result.reply });

    if (result.session_id && !currentSessionId) {
      currentSessionId = result.session_id;
      if (headerTitle) headerTitle.textContent = result.title || "New Chat";
      loadSessions();
    }

    speak(result.reply);

  } catch (err) {
    typingEl.remove();
    setStatus("", "Ready");
    addMessage("❌ " + err.message, "bot");
    showToast("Server error");
  }
}

// ─── API WITH AUTH ───
async function fetchAIResponse(userText) {
  if (!TOKEN) throw new Error("Not logged in");

  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${TOKEN}`
    },
    body: JSON.stringify({
      message: userText,
      session_id: currentSessionId
    }),
  });

  if (response.status === 401) {
    localStorage.removeItem("nova_token");
    localStorage.removeItem("nova_email");
    window.location.href = "login.html";
    throw new Error("Session expired");
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

// ─── SESSIONS ───
function startNewChat() {
  currentSessionId = null;
  conversationHistory = [];
  chatBox.innerHTML = '';
  if (welcomeScreen) welcomeScreen.style.display = "flex";
  if (headerTitle) headerTitle.textContent = "New Chat";
  textInput.value = '';
}

async function loadSessions() {
  if (!sessionsList) return;

  try {
    const res = await fetch(`${BACKEND_URL}/sessions`, {
      headers: { "Authorization": `Bearer ${TOKEN}` }
    });

    if (res.status === 401) {
      window.location.href = "login.html";
      return;
    }

    const sessions = await res.json();
    sessionsList.innerHTML = '';

    if (sessions.length === 0) {
      sessionsList.innerHTML = '<div style="padding:12px; color:var(--muted); font-size:0.8rem;">No chats yet</div>';
      return;
    }

    sessions.forEach(session => {
      const div = document.createElement('div');
      div.className = 'session-item' + (session.id === currentSessionId ? ' active' : '');
      div.innerHTML = `
        <span onclick="loadSession(${session.id})">${session.title}</span>
        <button onclick="deleteSession(${session.id})" class="icon-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      `;
      sessionsList.appendChild(div);
    });
  } catch (err) {
    console.error("Error loading sessions:", err);
  }
}

async function loadSession(sessionId) {
  try {
    const res = await fetch(`${BACKEND_URL}/sessions/${sessionId}/messages`, {
      headers: { "Authorization": `Bearer ${TOKEN}` }
    });

    const messages = await res.json();
    currentSessionId = sessionId;
    conversationHistory = messages;

    chatBox.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = "none";

    messages.forEach(msg => {
      addMessage(msg.content, msg.role === "assistant" ? "bot" : "user");
    });

    if (headerTitle) headerTitle.textContent = messages.length > 0 ? "Chat loaded" : "New Chat";
    loadSessions();
  } catch (err) {
    showToast("Failed to load chat");
  }
}

async function deleteSession(sessionId) {
  if (!confirm("Delete this chat?")) return;

  try {
    const res = await fetch(`${BACKEND_URL}/sessions/${sessionId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${TOKEN}` }
    });

    if (currentSessionId === sessionId) startNewChat();
    loadSessions();
    showToast("Chat deleted");
  } catch (err) {
    showToast("Error deleting chat");
  }
}

// ─── UI HELPERS ───
function addMessage(text, role) {
  const div = document.createElement("div");

  div.className = role === "bot"
    ? "message bot"
    : "message user";

  div.style.display = "block";
  div.style.visibility = "visible";
  div.style.opacity = "1";

  div.textContent = text;

  chatBox.appendChild(div);

  chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingIndicator() {
  const div = document.createElement("div");
  div.className = "typing-indicator";
  div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div;
}

function setStatus(mode, label) {
  statusPill.className = `status-pill ${mode}`;
  statusText.textContent = label;
}

function showToast(msg, duration = 3000) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), duration);
}

function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  const voices = window.speechSynthesis.getVoices();
  if (voices.length) utterance.voice = voices.find(v => v.lang === "en-US") || voices[0];
  window.speechSynthesis.speak(utterance);
}

function toggleSidebar() {
  sidebar.classList.toggle("collapsed");
}

function sendChip(el) {
  const text = el.textContent.replace(/^[^\s]+ /, '');
  handleUserMessage(text);
}

function logout() {
  localStorage.removeItem("nova_token");
  localStorage.removeItem("nova_email");
  window.location.href = "login.html";
}

window.addEventListener("load", () => {
  loadSessions();
});
