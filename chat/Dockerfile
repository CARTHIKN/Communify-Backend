FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


COPY . /app/

RUN pip install gunicorn


CMD ["bash", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 chat.asgi:application"]
