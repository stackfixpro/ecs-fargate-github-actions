FROM python:3.13-slim

WORKDIR /app

# Install the libraries first, so Docker can reuse this layer when only app.py changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Don't run as root inside the container.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
