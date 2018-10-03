FROM python:2.7-alpine

MAINTAINER Shyam Sundar C S <csshyamsundar@gmail.com>

ENV PYTHONUNBUFFERED=0

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /app
COPY dnsproxy.py /app

EXPOSE 53

CMD ["python", "dnsproxy.py"]