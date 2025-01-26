FROM python:3.12

WORKDIR /

COPY src/requirements.txt /

RUN mkdir -p /app
COPY src/main.py /app
COPY src/__init__.py /app

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8888

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]