FROM python:3.11-slim

# FROM python:3.9-alpine


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \  
    && rm -rf /var/lib/apt/lists/*




WORKDIR /app




COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

COPY /app .

# ENV FLASK_APP=main.py

ENTRYPOINT [ "python", "main.py"]

# FROM python:3.6
# EXPOSE 5000
# ADD . /app

# WORKDIR /app

# COPY requirements.txt /app

# RUN pip install -r requirements.txt

# COPY main.py /app
# CMD python main.py
