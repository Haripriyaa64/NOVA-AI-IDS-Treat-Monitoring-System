/* ===========================
   NOVA — AI Voice Assistant
   script.js
=========================== */

// ─── CONFIG ───────────────────────────────────────────────────────────────
const BACKEND_URL = "http://127.0.0.1:8000/chat";

// ─── ELEMENTS ─────────────────────────────────────────────────────────────
const chatBox       = document.getElementById("chat");
const micBtn        = document.getElementById("micBtn");
const statusPill    = document.getElementById("statusPill");
const statusText    = document.getElementById("statusText");
const textInput     = document.getElementById("textInput");
const welcomeScreen = document.getElementById("welcomeScreen");
const toast         = document.getElementById("toast");

// ─── CONVERSATION MEMORY ──────────────────────────────────────────────────
// Stores the full chat history so the AI has context across turns
const conversationHistory = [];

// ─── SPEECH RECOGNITION SETUP ─────────────────────────────────────────────
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition = null;
let isListening  = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.continuous     = false;
  recognition.maxAlternatives = 1;

  // ✅ FIX: Guard against double-start races
  recognition.onstart = () => {
    isListening = true;
    setStatus("listening", "Listening…");
    micBtn.classList.add("listening");
  };

  recognition.onresult = async (event) => {
    const userText = event.results[0][0].transcript.trim();
    if (!userText) return;
    handleUserMessage(userText);
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove("listening");
    if (statusText.textContent === "Listening…") {
      setStatus("", "Ready");
    }
  };

  // ✅ FIX: Proper error codes with helpful messages
  recognition.onerror = (event) => {
    isListening = false;
    micBtn.classList.remove("listening");
    setStatus("", "Ready");

    const errorMessages = {
      "no-speech":    "⚠️ No speech detected — please try again.",
      "not-allowed":  "🚫 Microphone access denied. Check browser permissions.",
      "audio-capture":"🎤 No microphone found. Connect one and try again.",
      "network":      "🌐 Network error during speech recognition.",
      "aborted":      null,   // user cancelled — silent
    };

    const msg = errorMessages[event.error];
    if (msg) showToast(msg);
  };
} else {
  // Browser doesn't support speech recognition
  micBtn.style.display = "none";
  showToast("⚠️ Browser doesn't support voice input. Use Chrome or Edge.");
}

// ─── MIC BUTTON ───────────────────────────────────────────────────────────
function startListening() {
  if (!recognition) return;

  if (isListening) {
    // Toggle off
    recognition.stop();
    return;
  }

  // ✅ FIX: Wrap in try/catch — prevents "already started" crash
  try {
    recognition.start();
  } catch (e) {
    console.warn("Recognition start error:", e.message);
    // If already started, stop and restart
    if (e.message.includes("already started")) {
      recognition.stop();
      setTimeout(() => recognition.start(), 300);
    }
  }
}

// ─── TEXT INPUT ───────────────────────────────────────────────────────────
function handleKey(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendText();
  }
}

function sendText() {
  const text = textInput.value.trim();
  if (!text) return;
  textInput.value = "";
  autoResize(textInput);
  handleUserMessage(text);
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

// ─── SUGGESTION CHIPS ─────────────────────────────────────────────────────
function sendChip(btn) {
  const text = btn.textContent.replace(/^[\p{Emoji}\s]+/u, "").trim();
  handleUserMessage(text);
}

// ─── CORE MESSAGE HANDLER ─────────────────────────────────────────────────
async function handleUserMessage(text) {
  // Hide welcome screen on first message
  if (welcomeScreen) welcomeScreen.style.display = "none";

  addMessage(text, "user");
  conversationHistory.push({ role: "user", content: text });

  setStatus("thinking", "Thinking…");
  const typingEl = addTypingIndicator();

  try {
    const reply = await fetchAIResponse(text);
    typingEl.remove();
    setStatus("", "Ready");

    addMessage(reply, "bot");
    conversationHistory.push({ role: "assistant", content: reply });

    speak(reply);
  } catch (err) {
    typingEl.remove();
    setStatus("", "Ready");
    console.error("Chat error:", err);

    const errMsg = getErrorMessage(err);
    addMessage(errMsg, "bot");
    showToast("⚠️ Could not reach the server.");
  }
}

// ─── API CALL WITH MEMORY ─────────────────────────────────────────────────
async function fetchAIResponse(userText) {
  const response = await fetch(BACKEND_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // Send full history so backend can pass it to Groq
    body: JSON.stringify({
      message: userText,
      history: conversationHistory.slice(-10)  // last 10 turns for context
    }),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.reply;
}

function getErrorMessage(err) {
  if (err.message.includes("Failed to fetch")) {
    return "❌ Cannot connect to server. Make sure your FastAPI backend is running on port 8000.";
  }
  return `❌ Error: ${err.message}`;
}

// ─── UI HELPERS ───────────────────────────────────────────────────────────
function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div;
}

function addTypingIndicator() {
  const div = document.createElement("div");
  div.className = "typing-indicator";
  div.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div;
}

function setStatus(mode, label) {
  statusPill.className = `status-pill ${mode}`;
  statusText.textContent = label;
}

function showToast(msg, duration = 3500) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), duration);
}

// ─── TEXT-TO-SPEECH ───────────────────────────────────────────────────────
function speak(text) {
  if (!window.speechSynthesis) return;

  // Cancel any in-progress speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang  = "en-US";
  utterance.rate  = 1.05;
  utterance.pitch = 1;

  // ✅ FIX: Chrome TTS bug — voices must be loaded first
  const setVoice = () => {
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v =>
      v.name.includes("Google") && v.lang === "en-US"
    ) || voices.find(v => v.lang === "en-US") || voices[0];

    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
  };

  if (window.speechSynthesis.getVoices().length > 0) {
    setVoice();
  } else {
    window.speechSynthesis.onvoiceschanged = setVoice;
  }
}