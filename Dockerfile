# Use official Python image
FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose ports (no inline comments)
EXPOSE 8000
EXPOSE 8501
