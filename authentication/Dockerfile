FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/


# COPY ./entrypoint.sh .

# RUN python manage.py collectstatic --noinput
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver"]