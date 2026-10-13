FROM python:3.15.0-alpine
LABEL maintainer="xz-dev <xiangzhedev@gmail.com>"

COPY . /app

RUN pip install --no-cache-dir -r /app/requirements.txt

ENTRYPOINT ["python", "/app/main.py"]
