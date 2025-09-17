# PageMiner

An intelligent web crawler and scraper that mines data from web pages using AI.

## Features

- **🕷️ Web Crawling**: Automatically discovers and follows hyperlinks
- **🤖 AI Extraction**: Describe what you want in plain English
- **🌐 Smart Scraping**: Handles JavaScript, filters unwanted content
- **⚙️ Flexible Setup**: Works with local ChromeDriver or remote services

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup ChromeDriver (Free Option)

```bash
# Download ChromeDriver from https://chromedriver.chromium.org/
# Extract to a folder and update .env file
```

### 3. Configure Environment

Copy `sample.env` to `.env` and set your preferred mode:

```bash
# For local ChromeDriver (free)
SCRAPING_MODE=local
CHROMEDRIVER_PATH=/path/to/chromedriver

# For remote service (paid)
SCRAPING_MODE=remote
SBR_WEBDRIVER=wss://your-service-url
```

### 4. Install Ollama (for AI parsing)

```bash
# Install Ollama from https://ollama.ai/
ollama pull llama3
```

### 5. Run the App

```bash
streamlit run main.py
```

## Usage

1. **Enter a website URL**
2. **Choose mode**: Single page or multi-page crawling
3. **Configure options**: Max pages, delays, domain restrictions
4. **Scrape content**: Click "Scrape Website"
5. **Extract data**: Describe what you want to find

## Examples

- "Extract all email addresses and phone numbers"
- "Find all product names and prices"
- "Get all job titles and company names"
- "List all article headlines and dates"

## Free vs Paid Setup

| Feature     | Local (Free)          | Remote (Paid) |
| ----------- | --------------------- | ------------- |
| Cost        | Free                  | $10-50/month  |
| Setup       | Download ChromeDriver | Just add URL  |
| CAPTCHA     | Manual                | Auto-solved   |
| IP Blocking | Possible              | Rare          |
| Performance | Good                  | Excellent     |
