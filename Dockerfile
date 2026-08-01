FROM python:3.11-slim

# Install OS deps if needed
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Use PORT environment variable from Cloud Run
ENV PORT=8080
EXPOSE 8080

# Use gunicorn to run the Flask app
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 app:app
