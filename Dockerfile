FROM python:3.8-slim-bullseye

WORKDIR /usr/src/sentinel

COPY . .

RUN pip install -r requirements.txt

CMD ["python","-u","launcher.py"]