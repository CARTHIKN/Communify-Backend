FROM python:3.10
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# RUN python manage.py collectstatic --noinput
RUN pip install gunicorn


CMD ["gunicorn", "--bind", "0.0.0.0:8001", "userside.wsgi:application"]