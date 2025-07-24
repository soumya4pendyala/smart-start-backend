# ---- Stage 1: Build ----
# Use an official Python image to create a build environment.
# Using a specific version is better for reproducibility.
FROM python:3.11-slim as builder

# Set the working directory
WORKDIR /app

# Install uv - the fast Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# Add uv to the PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Create a virtual environment using uv
# This isolates dependencies within a specific folder
RUN uv venv

# Copy the requirements file first to leverage Docker's layer caching.
# The layer will only be rebuilt if requirements.txt changes.
COPY requirements.txt .

# Install dependencies into the virtual environment
# The ". .venv/bin/activate" part is not strictly needed as `uv pip` can target the venv,
# but this pattern is clear. We use --system to install into the venv python.
RUN uv pip install --no-cache-dir -r requirements.txt --system

# ---- Stage 2: Final Image ----
# Use the same slim base image for a smaller final image size
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Create a non-root user and switch to it for better security
RUN useradd --create-home appuser
USER appuser

# Copy the virtual environment with all the installed packages from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy your application code into the container
# This should be one of the last steps
COPY . .

# Update the PATH to use the executables from the virtual environment
ENV PATH="/app/.venv/bin:${PATH}"

# Expose port 8000 to allow traffic to the container
EXPOSE 8000

# Define the command to run the Uvicorn server
# Use 0.0.0.0 as the host to make it accessible from outside the container.
# Assuming your main Python file is named `main.py` and your FastAPI instance is `app`.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]