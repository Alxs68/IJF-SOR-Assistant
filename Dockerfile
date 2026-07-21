# Use official Python lightweight image
FROM python:3.12-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory inside container
WORKDIR /app

# Install system dependencies (specifically Graphviz for Streamlit UI rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies manifest
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire workspace code (excluding items in .dockerignore / .gitignore)
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Run Streamlit application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
