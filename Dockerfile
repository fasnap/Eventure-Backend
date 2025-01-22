# Use an official Python runtime as a parent image
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYCODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# requirements file from project directory to container
COPY ./requirements.txt /app/

# Upgrade pip and install production dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY ./eventure /app 

# Expose the necessary port
EXPOSE 8000

# Start the application with Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "eventure.asgi:application"]