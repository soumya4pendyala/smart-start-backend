# Use an official Python runtime as a parent image
FROM python:3.13-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# Create a requirements.txt if you don't have one:
# pip freeze > requirements.txt in your backend venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Uvicorn will listen on
# Cloud Run will automatically map external traffic to this port
ENV PORT 8000
EXPOSE 8000

# Run the Uvicorn server when the container launches
# --host 0.0.0.0 is crucial for listening on all interfaces in a container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]