FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/ /app/src
WORKDIR /app/src

RUN python manage.py makemigrations && python manage.py migrate && python manage.py shell < app/create_user.py

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]