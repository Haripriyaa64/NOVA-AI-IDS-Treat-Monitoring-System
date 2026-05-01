# 🚀 NOVA — AI Voice Assistant

NOVA is a full-stack AI-powered voice assistant that enables real-time voice interaction using speech-to-text, intelligent AI responses, and text-to-speech output. It delivers a smooth conversational experience similar to modern AI assistants.

---

## 🌟 Key Highlights

* 🎤 Real-time Voice Input (Speech-to-Text)
* 🤖 Intelligent AI Chatbot (Context-aware)
* 🔊 Voice Output (Text-to-Speech)
* ⚡ Fast & Lightweight Backend (FastAPI)
* 🔐 Secure API Handling (.env protection)
* 💬 Interactive Chat UI with Animations
* 🌐 Full Stack Project (Frontend + Backend)

---

## 📸 Screenshots

### 💬 Chat Interface

<img width="1202" height="860" alt="image" src="https://github.com/user-attachments/assets/8e3bd635-34c2-4b6b-8ae2-185dee92a0a6" />



### 🤖 AI Response

<img width="943" height="844" alt="image" src="https://github.com/user-attachments/assets/a457f229-f202-4ca9-8ed9-9f1394bae94a" />

---

## 🧠 System Workflow

```
User speaks 🎤
   ↓
SpeechRecognition (Browser)
   ↓
Text sent to Backend (FastAPI)
   ↓
AI Model via Groq API
   ↓
Response generated 🤖
   ↓
Returned to Frontend
   ↓
Text-to-Speech 🔊
   ↓
Displayed in Chat UI 💬
```

---

## 🏗️ Tech Stack

### 🔹 Frontend

* HTML5
* CSS3 (Animations, UI Design)
* JavaScript
* Web Speech API:

  * SpeechRecognition (STT)
  * SpeechSynthesis (TTS)

---

### 🔹 Backend

* Python
* FastAPI
* Uvicorn Server

---

### 🔹 AI Integration

* Groq API
* LLaMA 3 / LLaMA 3.1 models

---

### 🔹 Security

* dotenv (.env file)
* GitHub Secret Protection
* CORS Middleware

---

### 🔹 Version Control

* Git & GitHub

---

## 📂 Project Structure

```
NOVA-AI-Voice-Assistant/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env  (ignored for security)
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── screenshots/
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 🔹 1. Clone Repository

```
git clone https://github.com/your-username/NOVA-AI-Voice-Assistant.git
cd NOVA-AI-Voice-Assistant
```

---

### 🔹 2. Backend Setup

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

Run backend:

```
uvicorn main:app --reload
```

---

### 🔹 3. Frontend Setup

Open:

```
frontend/index.html
```

OR use Live Server in VS Code

---

## 🔐 Security Best Practices

* ❌ Never push `.env` to GitHub
* ✔ Use `.gitignore`
* ✔ Rotate API keys if exposed
* ✔ Use environment variables in deployment


---

## 🚀 Future Enhancements

* 👤 User Authentication (Login/Signup)
* 🗄️ Database Integration (MongoDB / PostgreSQL)
* 📜 Chat History Storage
* 🌍 Multi-language Voice Support
* 📱 Mobile Responsive UI
* ☁️ Cloud Deployment (AWS / Docker)
* 🎯 Custom AI Fine-tuning

---

## 🎯 Learning Outcomes

This project demonstrates:

* Full Stack Development
* API Integration
* AI Application Development
* Voice Interface Design
* Secure Coding Practices

---

## 👩‍💻 Author

Haripriya Pawar


---

## ⭐ Support

If you found this useful:

* ⭐ Star the repository
* 🍴 Fork and contribute
* 📢 Share with others

---

## 📜 License

This project is for educational purposes.
