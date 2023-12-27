FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY . .

CMD [ "gunicorn", "app:app", "-b", "0.0.0.0:5000" ]