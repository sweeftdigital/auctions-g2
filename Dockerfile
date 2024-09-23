FROM python:3.10.12

ENV PYTHONDONTWRITEBUFFERCODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /auctions

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001
