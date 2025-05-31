from engineio.async_drivers import threading
from flask import Flask, request, jsonify, render_template
from gtts import gTTS
import os
from datetime import datetime
from flask_cors import CORS
import base64
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)  # تمكين CORS للجميع

# تهيئة SocketIO مع إصدارات متوافقة
socketio = SocketIO(app,
                  cors_allowed_origins="*",
                  async_mode='threading',
                  engineio_logger=True,
                  logger=True,
                  ping_timeout=60,
                  ping_interval=25,
                  allow_upgrades=False,  # تعطيل الترقية التلقائية
                  transports=['websocket'])  # السماح فقط بـ WebSocket

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/socket.io/')
def handle_socketio():
    return socketio.handle_request(request)

@app.route('/socket.io/<path:path>')
def handle_socketio_path(path):
    return socketio.handle_request(request)

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        # معالجة البيانات الواردة
        if request.content_type == 'application/json':
            data = request.get_json()
            text = data.get('text', '')
        else:
            text = request.form.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"speech_{timestamp}.mp3"
        
        # إنشاء ملف الصوت
        tts = gTTS(text=text, lang='ar', slow=False)
        tts.save(filename)
        
        # قراءة وتحويل الصوت
        with open(filename, 'rb') as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        
        # إرسال عبر WebSocket
        socketio.emit('new_audio', {
            'text': text,
            'audio': audio_base64,
            'timestamp': timestamp
        }, namespace='/')
        
        return jsonify({
            'status': 'success',
            'text': text,
            'timestamp': timestamp
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# أحداث SocketIO
@socketio.on('connect', namespace='/')
def handle_connect():
    print(f'عميل متصل: {request.sid}')
    emit('connection_ack', {'message': 'تم الاتصال بنجاح'})

@socketio.on('disconnect', namespace='/')
def handle_disconnect():
    print(f'عميل انقطع: {request.sid}')

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # لو Railway موفرش PORT، يستخدم 5000 محلياً
    socketio.run(app,
                 host='0.0.0.0',
                 port=port,
                 debug=False)

