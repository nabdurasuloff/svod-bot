"""Telegram bot (webhook, Cloud Run). Omborni yuborasiz -> 6 ta jadval qaytadi."""
import os, tempfile, threading, shutil, traceback, collections
import requests
from flask import Flask, request, abort
from svodbot.pipeline import run, guess_date

TOKEN = os.environ['TELEGRAM_TOKEN']
SECRET = os.environ.get('WEBHOOK_SECRET', '')
ALLOWED = {int(x) for x in os.environ.get('ALLOWED_IDS', '').replace(' ', '').split(',') if x}
API = f'https://api.telegram.org/bot{TOKEN}'
app = Flask(__name__)
LOCK = threading.Lock()
SEEN = collections.deque(maxlen=500)


def say(chat, text):
    requests.post(f'{API}/sendMessage', json={'chat_id': chat, 'text': text}, timeout=30)


def process(chat, doc, caption):
    if not LOCK.acquire(blocking=False):
        return say(chat, '⏳ Ҳозир бошқа файл ишланяпти, 5 дақиқадан кейин юборинг.')
    tmp = tempfile.mkdtemp(prefix='job_')
    try:
        if doc.get('file_size', 0) > 20 * 1024 * 1024:
            return say(chat, 'Файл 20 МБ дан катта — Telegram бундай файлни бота бермайди.')
        say(chat, '⏳ Қабул қилинди, тўлдиряпман (2–4 дақиқа)…')
        info = requests.get(f'{API}/getFile', params={'file_id': doc['file_id']}, timeout=60).json()['result']
        src = os.path.join(tmp, 'ombor.xlsx')
        with requests.get(f'https://api.telegram.org/file/bot{TOKEN}/{info["file_path"]}', stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(src, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        date = guess_date(doc.get('file_name', ''), caption)
        final, counts, notes = run(src, os.path.join(tmp, 'out'), date)
        for k in sorted(final):
            with open(final[k], 'rb') as fh:
                requests.post(f'{API}/sendDocument', data={'chat_id': chat}, files={'document': (os.path.basename(final[k]), fh)}, timeout=300)
        names = {1: 'Доимий иш', 2: 'Субсидия/ссуда', 3: 'Кредит', 4: 'Касб-ҳунар', 5: 'ЯТТ/Деҳқон', 6: 'Ўзини ўзи банд'}
        txt = f'✅ {date} учун тайёр.\n' + '\n'.join(f'{k}. {names[k]}: {counts[k]}' for k in sorted(counts))
        if notes:
            txt += '\n\nДиққат:\n' + '\n'.join('• ' + n for n in notes)
        say(chat, txt)
    except Exception as e:
        traceback.print_exc()
        say(chat, f'❌ Хатолик: {str(e)[:300]}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        LOCK.release()


@app.route('/', methods=['GET'])
def health():
    return 'ok'


@app.route('/webhook', methods=['POST'])
def webhook():
    if SECRET and request.headers.get('X-Telegram-Bot-Api-Secret-Token') != SECRET:
        abort(403)
    u = request.get_json(force=True, silent=True) or {}
    if u.get('update_id') in SEEN:
        return 'ok'
    SEEN.append(u.get('update_id'))
    m = u.get('message') or {}
    chat = (m.get('chat') or {}).get('id')
    uid = (m.get('from') or {}).get('id')
    if not chat:
        return 'ok'
    if uid not in ALLOWED:
        say(chat, f'Рухсат йўқ. Сизнинг ID: {uid}\nАдминистраторга юборинг.')
        return 'ok'
    if m.get('document'):
        d = m['document']
        if not str(d.get('file_name', '')).lower().endswith('.xlsx'):
            say(chat, 'Илтимос, «Омбор китоби» .xlsx файлини юборинг.')
        else:
            threading.Thread(target=process, args=(chat, d, m.get('caption', '')), daemon=True).start()
    else:
        say(chat, 'Омбор китоби (.xlsx) файлини юборинг — 6 та жадвални тайёрлаб бераман. Сана керак бўлса, файл остига «28.10» деб ёзинг.')
    return 'ok'
