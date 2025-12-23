
from typing import Any

import feedparser
from typing import List, Dict
import requests
import json
import os
import logging
from datetime import datetime
import asyncio

import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from dotenv import load_dotenv
load_dotenv() # Load the variables


RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
]

async def fetch_news_from_rss() -> List[Dict]:
    """Fetch latest news articles from NYT and WSJ RSS feeds"""
    articles = []

    try: 
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:5]:
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
        logging.info(f"Error: RSS request incomplete: {e}")
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
            1. Brief introduction
            2. Pick 10 key stories grouped by theme 
            3. For each story: headline, 2-4 sentence summary, link
            4. Professional but friendly tone
            5. Keep the title emoji free 

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
       logging.info(f"Error calling LLM: {e}")

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
        msg['Date'] = str(datetime.date.today())

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_FROM, SMTP_PASSWORD)
            server.sendmail(
                EMAIL_FROM, EMAIL_TO, msg.as_string()
            )
        print(f"✅ Email sent successfully to {EMAIL_TO}")
        return True
    
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
        

async def main():
    articles = await fetch_news_from_rss()
    summary = generate_summary_with_claude(articles)

    date = datetime.now().strftime("%d/%m/%Y")
    subject = f"[URGENT] Daily News for {date}"
    success = send_email(subject, summary)

if __name__ == "__main__":
    asyncio.run(main())
    