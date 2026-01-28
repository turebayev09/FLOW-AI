import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

api_key = os.environ.get('GOOGLE_API_KEY')
client = None
if api_key:
    client = genai.Client(api_key=api_key)

MENTOR_PROMPT = "Ты — профессиональный ИИ-ментор по Python. Помогай ученику найти ошибку самому через вопросы."
SOLUTION_PROMPT = "Ты — эксперт по Python. Просто перепиши присланный код правильно без объяснений."

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>FLOW AI - Login & Mentor</title>
        <meta charset="utf-8">
        <script type="module">
          import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
          import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

          const firebaseConfig = {
            apiKey: "AIzaSyBghFUIfqr3GdUz5G7vf04gpoOPa0gVWo8",
            authDomain: "flow-ai-ccc5c.firebaseapp.com",
            projectId: "flow-ai-ccc5c",
            storageBucket: "flow-ai-ccc5c.firebasestorage.app",
            messagingSenderId: "384050736910",
            appId: "1:384050736910:web:884771f316b3b681f9715f",
            measurementId: "G-FYSRWN6Q3G"
          };

          const app = initializeApp(firebaseConfig);
          const auth = getAuth(app);
          const provider = new GoogleAuthProvider();

          window.login = () => {
              signInWithPopup(auth, provider)
                 .then((result) => console.log("Logged in:", result.user))
                 .catch((error) => alert(error.message));
          };

          window.logout = () => signOut(auth);

          onAuthStateChanged(auth, (user) => {
              const loginScreen = document.getElementById('login-screen');
              const mainApp = document.getElementById('main-app');
              const userEmail = document.getElementById('user-email');

              if (user) {
                  loginScreen.style.display = 'none';
                  mainApp.style.display = 'block';
                  userEmail.textContent = "Пользователь: " + user.email;
              } else {
                  loginScreen.style.display = 'block';
                  mainApp.style.display = 'none';
              }
          });
        </script>

        <style>
            body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center; }
           .container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); width: 100%; max-width: 800px; }
            h1 { color: #667eea; text-align: center; }
            textarea { width: 100%; height: 200px; padding: 15px; border-radius: 8px; border: 2px solid #eee; font-family: monospace; }
           .btn-group { display: flex; gap: 10px; margin-top: 20px; }
            button { flex: 1; padding: 15px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; color: white; transition: 0.2s; }
           .login-btn { background: #4285F4; width: 100%; }
           .mentor-btn { background: #3498db; }
           .sol-btn { background: #2ecc71; }
           .logout-link { color: #666; cursor: pointer; text-decoration: underline; font-size: 12px; }
            #result { margin-top: 20px; padding: 15px; background: #f9f9f9; border-left: 4px solid #667eea; display: none; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <div class="container">
            <div id="login-screen">
                <h1>FLOW AI</h1>
                <p style="text-align:center">Пожалуйста, войдите, чтобы использовать ИИ-наставника</p>
                <button onclick="login()" class="login-btn">Войти через Google</button>
            </div>

            <div id="main-app" style="display:none">
                <div style="display:flex; justify-content: space-between; align-items: center">
                    <h1>FLOW AI</h1>
                    <div>
                        <span id="user-email" style="font-size: 12px; color: #666"></span><br>
                        <span onclick="logout()" class="logout-link">Выйти</span>
                    </div>
                </div>
                
                <textarea id="codeInput" placeholder="# Вставьте ваш Python код здесь..."></textarea>
                
                <div class="btn-group">
                    <button onclick="processCode('mentor')" class="mentor-btn"> Анализ кода</button>
                    <button onclick="processCode('solution')" class="sol-btn"> Решение</button>
                </div>
                
                <div id="result"></div>
            </div>
        </div>

        <script>
        async function processCode(mode) {
            const code = document.getElementById('codeInput').value;
            const resultDiv = document.getElementById('result');
            
            if (!code.trim()) return alert('Введите код!');

            resultDiv.style.display = 'block';
            resultDiv.textContent = '⏳ Обработка...';

            try {
                // ВАЖНО: Когда задеплоишь на Render, замени '/' на свою ссылку 'https://...onrender.com/analyze'
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, mode: mode })
                });
                const data = await response.json();
                resultDiv.textContent = (mode === 'mentor'? '💡 Совет:\\n' : '✅ Код:\\n') + data.advice;
            } catch (e) {
                resultDiv.textContent = 'Ошибка соединения.';
            }
        }
        </script>
    </body>
    </html>
    """

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_code():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    if not client:
        return jsonify({'advice': 'Ошибка: API ключ не настроен на сервере.'}), 500
    
    data = request.json
    mode = data.get('mode', 'mentor')
    user_code = data.get('code', '')
    
    system_instr = MENTOR_PROMPT if mode == 'mentor' else SOLUTION_PROMPT
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_code,
            config=types.GenerateContentConfig(
                system_instruction=system_instr,
                temperature=0.7 if mode == 'mentor' else 0.1
            )
        )
        return jsonify({'advice': response.text})
    except Exception as e:
        return jsonify({'advice': f'Ошибка ИИ: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)