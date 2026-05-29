# ==========================================
# PE AI - YOLOv8-pose Video Processing Service
# CPU Optimized Dockerfile
# ==========================================

# Use a lightweight python image
FROM python:3.10-slim

# Set environment variables
# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# OMP/MKL optimization for CPU-only containers (prevents CPU core thrashing)
ENV OMP_NUM_THREADS=2
ENV MKL_NUM_THREADS=2

# Set working directory
WORKDIR /app

# Install system dependencies required by OpenCV and package management
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only version first to keep the image extremely lightweight (~600MB vs 3GB+)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements file and install the rest of dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Create necessary directories for local media storage
RUN mkdir -p uploads homework

# Expose FastAPI port (Hugging Face Spaces default port is 7860)
EXPOSE 7860

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
