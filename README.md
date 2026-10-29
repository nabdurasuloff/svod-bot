# svod-bot — «Омбор китоби»дан 6 та жадвални автоматик тўлдириш

Telegram ботга Омбор файлини (`.xlsx`) юборасиз → 2–4 дақиқада 6 та тайёр жадвал қайтади:
1. Доимий ишга жойлаштирилди · 2. Субсидия/ссуда · 3. Кредит · 4. Касб-ҳунар · 5. ЯТТ/Деҳқон · 6. Ўзини ўзи банд (соҳалар кесимида).

Устунлар сарлавҳа матни бўйича аниқланади — Омбор устунлари жойи ўзгарса ҳам ишлайди.
Файл остига сана ёзиш мумкин (`28.10`); ёзилмаса файл номидан, у ҳам бўлмаса бугунги сана олинади.

## Тузилиши
| Йўл | Вазифаси |
|---|---|
| `bot.py` | Telegram webhook (Flask) |
| `svodbot/ombor.py` | Омборни ўқиш, устунларни аниқлаш, белгиларни (такрорий = 0) ҳисобга олиш |
| `svodbot/tables.py` | 6 шаблонни тўлдириш (кредит турлари: МЛ → Маҳалла лойиҳаси, ББҚ → Бизнесга биринчи қадам) |
| `svodbot/sector6.py`, `sect1.py` | Соҳа аниқлаш қоидалари (6- ва 1-жадвал) |
| `svodbot/lo.py`, `inject.py` | LibreOffice билан ҳисоблаш ва қийматларни файлга ёзиш |
| `assets/` | Шаблонлар (`t1..t6.xlsx`, тозаланган) ва МФЙ кодлари |

## Шахсий маълумотлар
Репозиторийда ЖШШИР/исм **йўқ**. Маълумотнома (`ref.pkl`: 21.10 хатлов тоифалари, реестр, фаолият турлари) Google Cloud Storage'да туради ва ботга муҳит ўзгарувчиси орқали уланади. `.gitignore` `*.pkl` ва Омбор файлларини ўтказмайди.

## Жойлаштириш (бир марта)
1. Google Cloud лойиҳасида API ларни ёқинг: Cloud Run, Cloud Build, Artifact Registry, Secret Manager, Cloud Storage.
2. Bucket очиб, `ref.pkl` ни юкланг:
   `gsutil mb -l europe-west1 gs://<BUCKET> && gsutil cp ref.pkl gs://<BUCKET>/ref.pkl`
3. Махфий қийматлар (Secret Manager): `telegram-token` (BotFather токени), `webhook-secret` (ихтиёрий узун матн), `allowed-ids` (рухсатли Telegram ID лар, вергул билан: `123,456`).
   Ўз ID ингизни билиш учун ботга ёзинг — «Рухсат йўқ. Сизнинг ID: …» деб жавоб беради.
4. Хизмат ҳисоби (service account) яратиб, роллар беринг: Cloud Run Admin, Cloud Build Editor, Service Account User, Storage Admin (bucket учун), Secret Manager Secret Accessor. JSON калитни GitHub'га қўйинг.
5. GitHub → Settings → Secrets and variables → Actions:
   - Secrets: `GCP_SA_KEY` (JSON калит), `GCP_PROJECT` (лойиҳа ID)
   - Variables: `REF_BUCKET` (bucket номи), `GCP_REGION` (масалан `europe-west1`)
6. `main` га push қилинг (ёки Actions → Deploy → Run workflow). Хизмат манзили чиқади.
7. Webhook ни улаш:
   `TELEGRAM_TOKEN=... WEBHOOK_SECRET=... ./scripts/set_webhook.sh https://svod-bot-xxxx.a.run.app`

Cloud Run'нинг service account'ига `ref.pkl` ўқиш/ёзиш ҳуқуқи (Storage Object Admin) керак.

## Локал ишга тушириш
```
pip install -r requirements.txt   # + libreoffice-calc
REF_PATH=ref/ref.pkl python -m svodbot.cli Омбор.xlsx --out out --date 28.10
```

## Маълум чекловлар
- Омборда йўқ маълумотлар тўлдирилмайди: 1-жадвалда ойлик иш ҳақи/корхоналар, 4-жадвалда ўқиш ҳолати (ваучер файли керак), 2- ва 5-жадвалларда сана (мавсум боши қўйилади).
- 6-жадвалда фаолият тури Омборда бўлмаса, аввалги Омбордан ЖШШИР бўйича олинади; топилмаса соҳа «Бошқа».
- МФЙ коди `assets/mfy.pkl` да топилмаса, код бўш қолади (ботнинг жавобида сони ёзилади).
