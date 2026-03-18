FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8008

ENV PORT=8008
ENV FLASK_DEBUG=0

CMD ["python", "app.py"]
