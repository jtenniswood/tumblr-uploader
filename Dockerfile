# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file first to take advantage of Docker layer caching
COPY requirements.txt /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files
COPY app.py /app

# We do not set environment variables for secrets here
# Instead, we rely on passing them at runtime or via a secrets manager

# Run the script
CMD ["python", "app.py"]
