FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-calc fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
# bitta ishchi: ishlar navbat bilan; threads — webhook javobi uchun
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 bot:app
