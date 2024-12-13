# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies (optional, if needed)
# RUN apt-get update && apt-get install -y <dependencies>

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8050

# Command to run your Dash app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "app:server"]

