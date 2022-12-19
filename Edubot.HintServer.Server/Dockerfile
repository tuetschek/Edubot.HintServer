FROM python:3.9-alpine

ENV PYTHONIOENCODING=utf-8

RUN mkdir /app
WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "app.py"]