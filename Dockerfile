FROM python:3.12.2-alpine
MAINTAINER xz <xiangzhedev@gmail.com>

COPY . /app

RUN pip install --no-cache-dir -r /app/requirements.txt

ENTRYPOINT ["python", "/app/main.py"]
