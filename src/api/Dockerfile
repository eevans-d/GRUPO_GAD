FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

# The base image already has uvicorn, gunicorn, and fastapi.
# We just need to install the other dependencies.

WORKDIR /app


# Copy requirements and install them
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./api /app
