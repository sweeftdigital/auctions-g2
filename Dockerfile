FROM python:3.10.12

ENV PYTHONDONTWRITEBUFFERCODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /auctions

COPY requirements.txt .

RUN apt-get update && apt-get install -y gettext
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "auctions.asgi:application"]
