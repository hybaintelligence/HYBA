# HYBA PQMC Reproducibility Environment
# This Dockerfile creates a deterministic environment for validating all HYBA results

FROM python:3.12.7-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY python_backend/requirements.txt /tmp/requirements.txt
COPY python_backend/requirements.test.txt /tmp/requirements.test.txt

# Install Python dependencies with exact versions
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.test.txt

# Install additional reproducibility tools
RUN pip install --no-cache-dir \
    jupyter==1.0.0 \
    matplotlib==3.8.0 \
    seaborn==0.13.0 \
    scipy==1.13.0 \
    pandas==2.2.0

# Copy source code
COPY python_backend /app/python_backend
COPY tests /app/tests
COPY reproducibility /app/reproducibility

# Set PYTHONPATH
ENV PYTHONPATH=/app/python_backend

# Set default seed for reproducibility
ENV PYTHONHASHSEED=42
ENV HYBA_REPRODUCIBILITY_MODE=true

# Create validation output directory
RUN mkdir -p /app/validation_output

# Default command
CMD ["python", "reproducibility/validate_all.py"]
