# Use an official Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies for Chrome and Selenium
RUN apt-get update && \
    apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg2 \
    ca-certificates \
    libx11-dev \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxrandr2 \
    libappindicator3-1 \
    libasound2 \
    fonts-liberation \
    libu2f-udev \
    libxss1 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install the stable version of Google Chrome
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Run the application with Gunicorn
CMD ["gunicorn", "--workers=4", "--timeout=120", "-b", "0.0.0.0:8080", "main:app"]
