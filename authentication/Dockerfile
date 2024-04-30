FROM python:3.10

WORKDIR /app

# Copy the requirements.txt file into the Docker image
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files
COPY . /app/
RUN pip install gunicorn

# Your CMD instruction
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 authentication.wsgi:application"]
