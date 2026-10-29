"""Маълумотнома (шахсий маълумотлар) — репозиторийда ЭМАС, Cloud Storage ёки локал файлда сақланади.
ref = {'cat21': {ПИНФЛ: тоифа}, 'reg': {ПИНФЛ: (сана, ...)}, 'act': {ПИНФЛ: фаолият тури}}"""
import os, pickle, io

BUCKET = os.environ.get('REF_BUCKET')
BLOB = os.environ.get('REF_BLOB', 'ref.pkl')
LOCAL = os.environ.get('REF_PATH', 'ref/ref.pkl')


def load():
    if BUCKET:
        from google.cloud import storage
        data = storage.Client().bucket(BUCKET).blob(BLOB).download_as_bytes()
        ref = pickle.load(io.BytesIO(data))
    else:
        ref = pickle.load(open(LOCAL, 'rb'))
    for k in ('cat21', 'reg', 'act'):
        ref.setdefault(k, {})
    return ref


def save(ref):
    data = pickle.dumps(ref)
    if BUCKET:
        from google.cloud import storage
        storage.Client().bucket(BUCKET).blob(BLOB).upload_from_string(data)
    else:
        os.makedirs(os.path.dirname(LOCAL) or '.', exist_ok=True)
        open(LOCAL, 'wb').write(data)
