# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY upload.py .

# Create data directories
RUN mkdir -p /data/upload /data/failed

# Set environment variables with defaults
ENV BASE_UPLOAD_FOLDER=/data/upload \
    FAILED_UPLOAD_BASE=/data/failed \
    POST_STATE=published \
    CAPTION_TEMPLATE="Find more inspiration at https://www.yourwebsite.com"

# Run the script when the container launches
CMD ["python", "upload.py"]
