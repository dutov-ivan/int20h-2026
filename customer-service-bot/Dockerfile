# 1. Base Image: Use an official Python runtime as a parent image
# "slim" variants are smaller and safer than full images, but easier to work with than Alpine.
FROM python:3.12-slim

# 2. Environment Variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Ensures python output is sent straight to terminal (logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. Work Directory
WORKDIR /app

# 4. System Dependencies (Optional but recommended)
# We update apt and install generic utilities if needed, then clean up to keep layer small.
# asyncpg usually installs fine on slim, but if you add other libs that need compiling, add 'build-essential'
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Dependency Installation (Layer Caching Strategy)
# We copy ONLY requirements.txt first. Docker will cache this layer.
# If you change your code but not your requirements, this step is skipped on rebuilds.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 6. Create a non-root user for security
# Running as root inside Docker is a security risk.
RUN useradd -m -u 1000 botuser

# 7. Copy Application Code
COPY . .

# 8. Ownership
# Ensure the non-root user owns the application files
RUN chown -R botuser:botuser /app

# 9. Switch to non-root user
USER botuser

# 10. Run the Application
# Using python -m ensures modules are resolved correctly
CMD ["python", "-m", "main"]