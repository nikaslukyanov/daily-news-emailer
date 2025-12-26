"""
Hugging Face-based news summarizer (Free alternative to Claude)
Uses models available on FREE Hugging Face Inference API
"""

import os
import requests
import logging
from typing import List, Dict
from huggingface_hub import InferenceClient
from openai import OpenAI



def generate_summary_with_huggingface(articles: List[Dict]) -> str:
    """Generate summary using Hugging Face Inference API (Free!)"""

    # Prepare articles text
    articles_text = "\n\n".join([
        f"Article {i+1}:\n"
        f"Title: {article['title']}\n"
        f"Source: {article.get('source', {}).get('name', 'Unknown')}\n"
        f"Description: {article.get('description', 'N/A')[:200]}\n"
        f"URL: {article.get('url', '')}"
        for i, article in enumerate(articles[:20])  # Limit to avoid context length
    ])

    prompt = f"""Create a concise, engaging daily news summary email.

            Articles:
            {articles}

            Format as an HTML email with:
            1. No introduction or conclusion.
            2. Keep the title emoji free  
            3. Pick at most 10 key stories grouped by theme. 
            4. Make sure that politics and markets are discussed. 
            4. For each story: headline, 2-4 sentence summary, link
            5. Professional but friendly tone
            
            Keep under 500 words."""

    try:
        client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key = os.environ.get("HF_KEY")
        )

        response = client.responses.create(
            model="openai/gpt-oss-120b:groq",
            instructions="You are a top journalist who cares about global affairs and markets",
            input=prompt    
        )

        html_content = response.output_text
        logging.info(f"Hugging Face response type: {type(html_content)}")

        # Strip markdown code fences if present
        if html_content.startswith("```html"):
            html_content = html_content.replace("```html", "", 1)
        if html_content.startswith("```"):
            html_content = html_content.replace("```", "", 1)
        if html_content.endswith("```"):
            html_content = html_content.rsplit("```", 1)[0]

        html_content = html_content.strip()

        if not html_content:
            logging.error(f"No content generated. Response: {result}")
            return 

        # Clean up markdown code fences if present
        if html_content.startswith("```html"):
            html_content = html_content.replace("```html", "", 1)
        if html_content.startswith("```"):
            html_content = html_content.replace("```", "", 1)
        if html_content.endswith("```"):
            html_content = html_content.rsplit("```", 1)[0]

        html_content = html_content.strip()

        logging.info("Summary generated successfully with Hugging Face")
        return html_content

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP Error calling Hugging Face: {e}")
        logging.error(f"Response: {e.response.text if e.response else 'No response'}")
        return
    except Exception as e:
        logging.error(f"Error calling Hugging Face: {e}")
        return 


# Alternative: Using Hugging Face Transformers locally (slower in GitHub Actions)
def generate_summary_local(articles: List[Dict]) -> str:
    """
    Generate summary using local Hugging Face model.
    WARNING: This is slow in GitHub Actions (10-30 seconds) and requires installing transformers.
    Only use if you want to avoid API calls entirely.
    """
    try:
        from transformers import pipeline

        # Use a small summarization model
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        # Combine articles
        articles_text = " ".join([
            f"{article['title']}. {article.get('description', '')}"
            for article in articles[:10]
        ])

        # Summarize
        summary = summarizer(articles_text, max_length=500, min_length=200, do_sample=False)

        html_content = f"<div><h2>Today's News Summary</h2><p>{summary[0]['summary_text']}</p></div>"

        logging.info("Summary generated with local model")
        return html_content

    except ImportError:
        logging.error("transformers library not installed. Install with: pip install transformers torch")
        return
    except Exception as e:
        logging.error(f"Error with local model: {e}")
        return
    
