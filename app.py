import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Настройка API ключа
api_key = os.environ.get('GOOGLE_API_KEY')
client = None
if api_key:
    client = genai.Client(api_key=api_key)

MENTOR_PROMPT = "Ты — профессиональный ИИ-ментор по Python. Помогай ученику найти ошибку самому через наводящие вопросы. Не давай готовый код сразу."
SOLUTION_PROMPT = "Ты — эксперт по Python. Просто перепиши присланный код правильно. Никаких объяснений, только чистый код."

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <title>FLOW AI - Ваш ИИ Наставник</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script type="module">
          import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
          import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

          const firebaseConfig = {
            apiKey: "AIzaSyBghFUIfqr3GdUz5G7vf04gpoOPa0gVWo8",
            authDomain: "flow-ai-ccc5c.firebaseapp.com",
            projectId: "flow-ai-ccc5c",
            storageBucket: "flow-ai-ccc5c.firebasestorage.app",
            messagingSenderId: "384050736910",
            appId: "1:384050736910:web:884771f316b3b681f9715f"
          };

          const app = initializeApp(firebaseConfig);
          const auth = getAuth(app);
          const provider = new GoogleAuthProvider();

          window.login = () => signInWithPopup(auth, provider).catch(e => alert(e.message));
          window.logout = () => signOut(auth);

          onAuthStateChanged(auth, (user) => {
              const loginScreen = document.getElementById('login-screen');
              const mainApp = document.getElementById('main-app');
              const userEmail = document.getElementById('user-email');

              if (user) {
                  loginScreen.style.display = 'none';
                  mainApp.style.display = 'block';
                  userEmail.textContent = user.email;
                  updateStatsUI();
              } else {
                  loginScreen.style.display = 'block';
                  mainApp.style.display = 'none';
              }
          });
        </script>

        <style>
            :root { --p-color: #667eea; --s-color: #764ba2; }
            body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, var(--p-color) 0%, var(--s-color) 100%); min-height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center; color: #333; }
            .container { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); width: 90%; max-width: 700px; }
            h1 { color: var(--p-color); text-align: center; margin-top: 0; }
            .stats-bar { background: #f0f4f8; padding: 12px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid var(--p-color); font-size: 14px; display: flex; justify-content: space-around; }
            textarea { width: 100%; height: 180px; padding: 15px; border-radius: 10px; border: 2px solid #eee; font-family: 'Consolas', monospace; box-sizing: border-box; resize: none; }
            .btn-group { display: flex; gap: 10px; margin-top: 15px; }
            button { flex: 1; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; }
            .login-btn { background: #4285F4; width: 100%; font-size: 16px; }
            .mentor-btn { background: #3498db; }
            .sol-btn { background: #2ecc71; }
            .logout-btn { color: #e74c3c; cursor: pointer; font-size: 12px; font-weight: bold; }
            #result { margin-top: 20px; padding: 15px; background: #fdfdfd; border-radius: 8px; border: 1px solid #eee; display: none; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div id="login-screen">
                <h1>FLOW AI</h1>
                <p style="text-align:center">Войдите в систему для доступа к ИИ-наставнику</p>
                <button onclick="login()" class="login-btn">Войти через Google</button>
            </div>

            <div id="main-app" style="display:none">
                <div style="display:flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <h2 style="margin:0; color:var(--p-color)">FLOW AI</h2>
                    <div style="text-align: right">
                        <span id="user-email" style="font-size: 11px; color: #888"></span><br>
                        <span onclick="logout()" class="logout-btn">Выйти</span>
                    </div>
                </div>

                <div class="stats-bar" id="stats-bar">
                    <span>Запросов: <b id="s-total">0</b></span>
                    <span>Ментор: <b id="s-mentor">0</b></span>
                    <span>Решений: <b id="s-sol">0</b></span>
                </div>
                
                <textarea id="codeInput" placeholder="# Вставьте ваш Python код здесь..."></textarea>
                
                <div class="btn-group">
                    <button onclick="processCode('mentor')" class="mentor-btn">Анализ кода</button>
                    <button onclick="processCode('solution')" class="sol-btn">Решение</button>
                </div>
                
                <div id="result"></div>
            </div>
        </div>

        <script>
        function updateStatsUI() {
            const stats = JSON.parse(localStorage.getItem('flow_stats')) || { t: 0, m: 0, s: 0 };
            document.getElementById('s-total').textContent = stats.t;
            document.getElementById('s-mentor').textContent = stats.m;
            document.getElementById('s-sol').textContent = stats.s;
        }

        async function processCode(mode) {
            const code = document.getElementById('codeInput').value;
            const resDiv = document.getElementById('result');
            if (!code.trim()) return alert('Пожалуйста, введите код!');

            resDiv.style.display = 'block';
            resDiv.innerHTML = '⏳ <i>ИИ обрабатывает запрос...</i>';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, mode: mode })
                });
                const data = await response.json();
                
                // Обновление локальной статистики
                let stats = JSON.parse(localStorage.getItem('flow_stats')) || { t: 0, m: 0, s: 0 };
                stats.t++;
                if(mode === 'mentor') stats.m++; else stats.s++;
                localStorage.setItem('flow_stats', JSON.stringify(stats));
                updateStatsUI();

                resDiv.innerHTML = `<b>${mode === 'mentor' ? '💡 Совет наставника:' : '✅ Готовое решение:'}</b>\\n\\n` + data.advice;
            } catch (e) {
                resDiv.textContent = 'Ошибка соединения с сервером.';
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
        return jsonify({'advice': 'Сервер: API ключ Gemini не найден в переменных окружения.'}), 500
    
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
        return jsonify({'advice': response.text.strip()})
    except Exception as e:
        return jsonify({'advice': f'Ошибка ИИ: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
