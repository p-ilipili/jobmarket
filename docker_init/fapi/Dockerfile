FROM python:3.9

WORKDIR /

ADD src/requirements.txt ./
ADD src/main.py ./app

RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8888

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]