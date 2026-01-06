# Daily News Emailer

An automated daily news digest service that fetches articles from major news sources, generates AI-powered summaries, and delivers them to your inbox.

## Features

- Fetches news from multiple RSS feeds (NY Times, Wall Street Journal, NPR) and NewsData API
- AI-powered summarization using Hugging Face (with Claude API as fallback)
- Automated daily email delivery via SMTP
- GitHub Actions integration for scheduled execution
- Organized by themes (Politics, Markets, Technology, etc.)
- Professional HTML email formatting

## How It Works

1. **News Collection**: Fetches articles from RSS feeds and NewsData API
2. **AI Summarization**: Uses Hugging Face's open-source models to generate concise summaries
3. **Fallback**: If Hugging Face fails, switches to Claude API
4. **Email Delivery**: Sends formatted HTML email via SMTP
5. **Automation**: Runs daily at 1 PM UTC via GitHub Actions

## Setup

### Prerequisites

- Python 3.11 or higher
- API keys for news services and AI models
- Email account with SMTP access (Gmail recommended)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd mcp_news/news
```

2. Install dependencies:
```bash
pip install requests feedparser python-dotenv huggingface-hub openai newsdataapi
```

3. Create a `.env` file with your credentials:
```env
# News API
NEWSDATAIO_API_KEY=your_newsdata_api_key

# AI Services
HF_KEY=your_huggingface_api_key
ANTHROPIC_API_KEY=your_claude_api_key

# Email Configuration
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_PASSWORD=your_app_specific_password
```

### GitHub Actions Setup

1. Go to your repository Settings > Secrets and variables > Actions
2. Add the following secrets:
   - `NEWSDATAIO_API_KEY`
   - `HF_KEY`
   - `ANTHROPIC_API_KEY`
   - `EMAIL_FROM`
   - `EMAIL_TO`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`

3. The workflow will run automatically every day at 1 PM UTC
4. You can also trigger it manually from the Actions tab

## Usage

### Run Locally

```bash
python daily_news_emailer.py
```

### Manual Trigger on GitHub

1. Go to the Actions tab in your repository
2. Select "Daily News Email" workflow
3. Click "Run workflow"

## Configuration

### News Sources

Modify `RSS_FEEDS` in `daily_news_emailer.py` to add or remove RSS sources:

```python
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    # Add your feeds here
]
```

### Email Customization

Adjust the summary prompt in `huggingface_summarizer.py` or `daily_news_emailer.py`:
- Number of stories (default: 10-15)
- Themes and categories
- Word count limit (default: 500 words)
- Tone and style

### Schedule

Change the cron schedule in `.github/workflows/daily-news.yml`:
```yaml
schedule:
  - cron: '0 13 * * *'  # Daily at 1 PM UTC
```

## Project Structure

```
news/
├── daily_news_emailer.py       # Main script
├── huggingface_summarizer.py   # AI summarization
├── pyproject.toml              # Project metadata
├── .env                        # Environment variables (local)
├── .github/
│   └── workflows/
│       └── daily-news.yml      # GitHub Actions workflow
└── README.md
```

## API Keys

### NewsData.io
Sign up at [newsdata.io](https://newsdata.io) for free news API access.

### Hugging Face
Get your API key at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### Anthropic Claude (Fallback)
Sign up at [console.anthropic.com](https://console.anthropic.com) for Claude API access.

### Gmail SMTP
Use an App Password instead of your regular password:
1. Enable 2-factor authentication on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Generate an App Password for "Mail"

## Troubleshooting

### Email Not Sending
- Verify SMTP credentials are correct
- For Gmail, ensure App Password is being used
- Check firewall/security settings

### No Articles Fetched
- Verify API keys are valid and have quota remaining
- Check RSS feed URLs are accessible
- Review GitHub Actions logs

### Summarization Errors
- Check Hugging Face API key validity
- Ensure Claude API key is set as fallback
- Review logs for specific error messages

## Dependencies

- `feedparser` - RSS feed parsing
- `requests` - HTTP requests
- `python-dotenv` - Environment variable management
- `huggingface-hub` - Hugging Face API client
- `openai` - OpenAI-compatible API client
- `newsdataapi` - NewsData.io API client

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
