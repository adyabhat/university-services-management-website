# Base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy everything into the container
COPY . .

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask's default port
EXPOSE 5001

# Run the app
CMD ["python", "app.py"]