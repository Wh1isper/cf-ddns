FROM python:3.12-slim

RUN apt-get update && apt-get install -y tini && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

COPY main.py /app/main.py

ENTRYPOINT ["tini", "--", "python"]
CMD ["main.py"]
