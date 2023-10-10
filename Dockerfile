# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Install PostgreSQL-Client
RUN apt-get update && apt-get install -y postgresql-client

# Expose the port your application will run on
EXPOSE 8000