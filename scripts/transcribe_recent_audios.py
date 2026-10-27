import subprocess
import requests
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

blobs = [
    (77, "fxvuwy9iiy29fwmwv7elrcz7oaba", "fx/vu/fxvuwy9iiy29fwmwv7elrcz7oaba"),
    (78, "fghrfrgffn5xqpkomg9xpic5wl9z", "fg/hr/fghrfrgffn5xqpkomg9xpic5wl9z"),
    (79, "8qiuyzvhvr1t360kp79rrl316ag2", "8q/iu/8qiuyzvhvr1t360kp79rrl316ag2"),
    (80, "xtq7tpsse8ce8ua21b3eegqt1skt", "xt/q7/xtq7tpsse8ce8ua21b3eegqt1skt")
]

for aid, key, path in blobs:
    # Copia o arquivo do container chatwoot para temp
    cmd = ['docker', 'exec', 'chatbot_n8n-chatwoot-web-1', 'cat', f'/app/storage/{path}']
    res = subprocess.run(cmd, capture_output=True)
    audio_data = res.stdout
    
    # Transcreve no Speaches
    files = {'file': ('audio.oga', audio_data, 'audio/ogg')}
    data = {'model': 'Systran/faster-whisper-small', 'language': 'pt'}
    try:
        r = requests.post('http://127.0.0.1:8000/v1/audio/transcriptions', files=files, data=data, timeout=15)
        text = r.json().get('text', '')
        print(f"=== Audio #{aid} (key: {key}) ===")
        print(f"Transcrição: \"{text}\"\n")
    except Exception as e:
        print(f"Erro no audio #{aid}: {e}")
