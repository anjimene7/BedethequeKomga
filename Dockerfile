# Use the official Python image from the Docker Hub
FROM python:3.10-slim-bullseye

RUN apt-get update
# Pyppeteer
ENV PUPPETEER_EXECUTABLE_PATH /usr/bin/chromium-browser
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    --no-install-recommends \
    && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    tesseract-ocr \
     zbar-tools \
    --no-install-recommends

# It won't run from the root user.
RUN groupadd chrome && useradd -g chrome -s /bin/bash -G audio,video chrome \
    && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install the required packages
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY log.py env.py get_proxies.py komgaApi.py processMetadata.py refreshMetadata.py bedethequeApi.py ./

# Set environment variables
ENV KOMGA_URL=$KOMGA_URL
ENV KOMGA_EMAIL=$KOMGA_EMAIL
ENV KOMGA_PASSWORD=$KOMGA_PASSWORD
ENV KOMGA_LIBRARY_LIST=$KOMGA_LIBRARY_LISTKOMGA_EMAIL
ENV KOMGA_COLLECTION_LIST=$KOMGA_COLLECTION_LIST
ENV KOMGA_SERIE_LIST=$KOMGA_SERIE_LIST
ENV KOMGA_STATUS=$KOMGA_STATUS
ENV KOMGA_SERIES_ONLY=$KOMGA_SERIES_ONLY
ENV KOMGA_WAIT_DELAY=$KOMGA_WAIT_DELAY
ENV KOMGA_USE_PROXIES=$KOMGA_USE_PROXIES
ENV KOMGA_DRY_RUN=$KOMGA_DRY_RUN

RUN python get_proxies.py
# Run the script
CMD ["python", "refreshMetadata.py"]
