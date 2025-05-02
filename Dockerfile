FROM python:3.11.4-buster

# Install dependencies including Chromium, curl, and unzip
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium and ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install the correct version of ChromeDriver based on the installed Chromium version
RUN CHROME_VERSION=$(chromium --version | awk '{print $2}' | cut -d '.' -f1-3) && \
    CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}) && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm chromedriver_linux64.zip

# Set the working directory to /app
WORKDIR /app

# Copy the Python dependencies file and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code to the container
COPY . .

# Set the command to run your Python app
CMD ["python", "bb_main.py"]