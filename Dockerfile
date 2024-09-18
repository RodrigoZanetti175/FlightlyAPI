FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

CMD ["gunicorn"  , "--workers=3", "--timeout=60", "-b", "0.0.0.0:8080", "main:app"]

# FROM cypress/browsers:latest
# RUN apt-get install python3 -y
# RUN echo $(python3 -m site --user-base)
# COPY requirements.txt .
# ENV PATH /home/root/.local/bin:${PATH}
# RUN apt-get update && apt-get install -y python3-pip && pip3 install -r requirements.txt	
# COPY . .
# CMD uvicorn main:app --host 0.0.0.0 --port 8000