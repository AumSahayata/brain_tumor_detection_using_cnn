# Use Python 3.11.9 as base image
FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire project
COPY . /app/

# Set Python path to include the current directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Create a script to run both services
RUN echo '#!/bin/bash\n\
cd /app && uvicorn backend.backend:app --host 0.0.0.0 --port 8000 &\n\
cd /app && streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0' > /app/start.sh \
&& chmod +x /app/start.sh

# Command to run the application
CMD ["/app/start.sh"] 