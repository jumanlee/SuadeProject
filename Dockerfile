FROM python:3.12-slim

#normally, python creates __pycache__/*.pyc files when it runs. In Docker, that’s useless bloat, so we need to disable it
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

#must do the following because this is python:3.12-slim, unlike the full python:3.12 image, it does not come with build tools like compilers baked in.
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

#copy app code
COPY . /app

EXPOSE 8000

#run with uvicorn + uvloop + httptools
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop", "--http", "httptools"]
