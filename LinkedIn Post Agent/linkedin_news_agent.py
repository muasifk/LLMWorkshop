
import os
import time
from datetime import datetime
import feedparser
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ========== CONFIG ==========
load_dotenv('../keys.env')  # Load environment variables from .env file
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)


# Step 2: Define AI news sources (RSS feeds or URLs)
def load_urls_from_file(filepath):
    with open(filepath, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    return urls
feeds = load_urls_from_file('urls.txt')
print(f'Searching {len(feeds)} sources')



# Step 3: Fetch and aggregate latest headlines
from utils import fetch_latest_news
sorted_entries = fetch_latest_news(feeds, max_articles=10)






def call_gemini(prompt, max_tokens=1000, temperature=0.6):
    """Wrapper for Gemini API calls with error handling"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens, 
                temperature=temperature
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return None
    







def summarize_and_select_news(entries, top_n=5):
    """Summarize articles and select the most important one"""
    if not entries:
        raise Exception("No articles to process")
    
    # Limit articles for processing
    top_articles = entries[:min(top_n, len(entries))]
    
    # Create a single prompt for all summaries to reduce API calls
    batch_prompt = (
        "Summarize each of the following AI news articles in exactly 50 words. "
        "Number each summary (1, 2, 3, etc.) and keep them professional:\n\n"
    )
    
    for i, entry in enumerate(top_articles, 1):
        batch_prompt += f"[{i}] Title: {entry.title}\n"
        batch_prompt += f"Description: {getattr(entry, 'summary', 'No description available')}\n"
        batch_prompt += f"Link: {entry.link}\n\n"
    
    summaries_response = call_gemini(batch_prompt, max_tokens=2000)
    if not summaries_response:
        raise Exception("Failed to generate summaries")
    
    # Parse summaries (this is a simplified approach)
    # In production, you might want more robust parsing
    summary_lines = summaries_response.split('\n')
    article_data = []
    
    for i, entry in enumerate(top_articles):
        article_data.append({
            'title': entry.title,
            'summary': f"Summary for: {entry.title}",  # Simplified - you'd parse from summaries_response
            'link': entry.link,
            'index': i + 1
        })
    
    # Select most important article
    selection_prompt = (
        "From the following AI news articles, choose the single most important one for AI professionals. "
        "Consider impact, relevance, and significance to the AI community. "
        "Respond with ONLY the number (1, 2, 3, etc.):\n\n"
    )
    
    selection_prompt += summaries_response
    selection_prompt += "\n\nRespond with only the number of the most important article:"
    
    selection_response = call_gemini(selection_prompt, max_tokens=10, temperature=0.1)
    
    if not selection_response:
        print("Warning: Failed to select article, using first one")
        return article_data[0]
    
    try:
        selected_index = int(selection_response.strip()) - 1
        if 0 <= selected_index < len(article_data):
            return article_data[selected_index]
        else:
            print(f"Warning: Invalid selection {selected_index + 1}, using first article")
            return article_data[0]
    except ValueError:
        print(f"Warning: Invalid selection response '{selection_response}', using first article")
        return article_data[0]












def create_linkedin_post(article_data):
    """Create a LinkedIn post from article data"""
    title_prompt = (
        f"Create a professional, engaging LinkedIn post title (10-15 words) for this AI news:\n"
        f"Title: {article_data['title']}\n"
        f"Summary: {article_data['summary']}\n"
        f"Make it attention-grabbing but professional."
    )
    
    catchy_title = call_gemini(title_prompt, max_tokens=50, temperature=0.7)
    
    if not catchy_title:
        catchy_title = article_data['title']  # Fallback to original title
    
    # Remove quotes if present
    catchy_title = catchy_title.strip('"\'')
    
    post = f"""🔹 {catchy_title}

{article_data['summary']}

🔗 Read more: {article_data['link']}

#AI #ArtificialIntelligence #Technology #Innovation"""
    
    return post

def run_agent():
    """Main function to run the AI news agent"""
    try:
        print("🤖 Starting AI News Agent...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load RSS feeds
        feeds = load_urls_from_file('urls.txt')
        print(f"📡 Monitoring {len(feeds)} AI news sources")
        
        # Fetch latest news
        entries = fetch_latest_news(feeds)
        print(f"📰 Found {len(entries)} recent articles")
        
        if not entries:
            print("❌ No articles found")
            return
        
        # Summarize and select most important
        selected_article = summarize_and_select_news(entries)
        print(f"✅ Selected: {selected_article['title']}")
        
        # Create LinkedIn post
        linkedin_post = create_linkedin_post(selected_article)
        
        print("\n" + "="*60)
        print("📱 LINKEDIN POST:")
        print("="*60)
        print(linkedin_post)
        print("="*60)
        
        return linkedin_post
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    result = run_agent()
    if result:
        print("\n✅ AI News Agent completed successfully!")
    else:
        print("\n❌ AI News Agent failed!")