# 1. Base image: lightweight Python runtime
FROM python:3.10-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Prevent Python from buffering standard I/O and creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Copy dependency requirements first (leverages Docker layer caching)
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Expose application port
EXPOSE 5000

# 8. Start application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]