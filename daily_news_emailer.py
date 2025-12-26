
from typing import Any

import feedparser
from typing import List, Dict
import requests
import json
import os
import logging
from datetime import datetime, timedelta, date
import asyncio

import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import http.client, urllib.parse

from newsdataapi import NewsDataApiClient
from huggingface_summarizer import generate_summary_with_huggingface


from dotenv import load_dotenv
load_dotenv() # Load the variables

# Configure logging to show in GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
    "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"
    "https://feeds.npr.org/1004/rss.xml"
]

async def fetch_news_from_raw_rss() -> List[Dict]:
    articles = []

    try: 
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                articles.append({
                    "title": entry.get("title", "Untitled"),
                    "description": entry.get("summary", entry.get("description", "")),
                    "url": entry.get("link", ""),
                    "source": {"name": feed.feed.get("title", "RSS Feed")},
                    "publishedAt": entry.get("published", ""),
                    "author": entry.get("author", "Unknown")
                })
            logging.info("RSS request complete")
    except Exception as e:
        logging.error(f"Error: RSS request incomplete: {e}")
    return articles

async def fetch_news_from_news_api() -> List[Dict]:
    articles = []

    try:
        API_KEY = os.environ.get("NEWSDATAIO_API_KEY")

        if not API_KEY:
            logging.error("NEWSDATAIO_API_KEY not found in environment variables!")
            return articles

        # Define link list AFTER getting API_KEY
        link_list = [
            f"https://newsdata.io/api/1/market?apikey={API_KEY}&q=market&language=en&domainurl=wsj.com,economist.com,bloomberg.com,ft.com,cnbc.com&sort=relevancy",
            f"https://newsdata.io/api/1/latest?apikey={API_KEY}&q=politics&language=en&domainurl=nytimes.com,wsj.com,theguardian.com,aljazeera.com&sort=relevancy"
        ]

        logging.info(f"Fetching news from {len(link_list)} API endpoints...")

        for i, url in enumerate(link_list, 1):
            logging.info(f"[{i}/{len(link_list)}] Fetching from NewsData API...")
            response = requests.get(url)
            data = response.json()

            # Check if request was successful
            if data.get('status') == 'success' and 'results' in data:
                count = len(data['results'])
                logging.info(f"Fetched {count} articles from endpoint {i}")

                # Parse each article from the response
                for item in data['results']:
                    articles.append({
                        "title": item.get("title", "Untitled"),
                        "description": item.get("description", ""),
                        "url": item.get("link", ""),
                        "source": {"name": item.get("source_id", "Unknown")},
                        "publishedAt": item.get("pubDate", ""),
                        "author": item.get("creator", ["Unknown"])[0] if item.get("creator") else "Unknown"
                    })
            else:
                logging.error(f"No results from endpoint {i}. Status: {data.get('status', 'unknown')}")
                if 'message' in data:
                    logging.error(f"API message: {data['message']}")

        logging.info(f"Total articles collected: {len(articles)}")

    except Exception as e:
        logging.error(f"Error: News API request incomplete: {e}")
    
    return articles

def generate_summary_with_claude(articles: List[Dict]) -> str:
    
    # Prepare articles with clear structure
    articles_text = "\n\n".join([
        f"Article {i+1}:\n"
        f"Headline: {article['title']}\n"
        f"Source: {article.get('source', {}).get('name', 'Unknown')}\n"
        f"Summary: {article.get('description', 'No description available')}\n"
        f"URL: {article.get('url', '')}\n"
        f"Published: {article.get('publishedAt', 'Unknown date')}"
        for i, article in enumerate(articles)
    ])
    
    prompt = f"""Create a concise, engaging daily news summary email.

            Articles:
            {articles}

            Format as an HTML email with:
            1. No introduction or conclusion.
            2. Keep the title emoji free  
            3. Pick at most 15 key stories grouped by theme. Make no more than 4 themes. 
            4. Make sure that politics and markets are discussed. 
            4. For each story: headline, 2-4 sentence summary, link
            5. Professional but friendly tone
            
            Keep under 500 words."""
    
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2000,
                "messages": [{
                    "role": "user", 
                    "content": prompt
                }]
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        html_content = result["content"][0]["text"]

        # Strip markdown code fences if present
        if html_content.startswith("```html"):
            html_content = html_content.replace("```html", "", 1)
        if html_content.startswith("```"):
            html_content = html_content.replace("```", "", 1)
        if html_content.endswith("```"):
            html_content = html_content.rsplit("```", 1)[0]

        html_content = html_content.strip()

        logging.info("Summary generate successfully")
        return html_content
    
    except Exception as e:
       logging.error(f"Error calling LLM: {e}")

def send_email(subject: str, html_content: str):
    EMAIL_TO = os.environ.get("EMAIL_TO", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Date'] = str(datetime.now().strftime("%Y-%m-%d"))

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_FROM, SMTP_PASSWORD)
            server.sendmail(
                EMAIL_FROM, EMAIL_TO, msg.as_string()
            )
        logging.info(f"Email sent successfully to {EMAIL_TO}")
        return True
    
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False
        

async def main():
    articles = await fetch_news_from_news_api()
    summary = generate_summary_with_huggingface(articles)

    # Fallback to Claude if Hugging Face fails
    if not summary or "Error" in summary:
        logging.warning("Error in HF: Fall back on Claude")
        summary = generate_summary_with_claude(articles)

    date = datetime.now().strftime("%d/%m/%Y")
    subject = f"Daily News for {date}"
    success = send_email(subject, summary)

if __name__ == "__main__":
    asyncio.run(main())
    