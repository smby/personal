import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import pytz
import logging
import time
from typing import List, Optional, Dict
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forum_monitor.log'),
        logging.StreamHandler()
    ]
)

class ForumMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # Set up headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def parse_post_time(self, time_str: str) -> Optional[datetime]:
        """
        Attempts to parse datetime string with different formats.
        
        Args:
            time_str: String representation of datetime
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
            "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format with microseconds
            "%Y-%m-%d %H:%M:%S%z"  # Standard format with timezone
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt).astimezone(timezone.utc)
            except ValueError:
                continue
        
        logging.error(f"Failed to parse post time: {time_str}")
        return None

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches and parses the page content with error handling and retries.
        
        Args:
            url: The URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetching fails
        """
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, "html.parser")
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
        
        logging.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    def format_post_data(self, posts: List[Dict], title: str) -> str:
        """
        Formats the post data for email content.
        
        Args:
            posts: List of post dictionaries
            title: Section title
            
        Returns:
            Formatted string of posts
        """
        if not posts:
            return ""
        
        formatted_posts = [f"**{title.upper()}**"]
        for post in posts:
            post_time_az = post['time'].astimezone(self.arizona_tz)
            formatted_posts.append(
                f"• {post['title']}\n"
                f"  Created: {post_time_az.strftime('%Y-%m-%d %H:%M:%S')} AZ Time\n"
                f"  Link: {post['link']}\n"
            )
        
        return "\n".join(formatted_posts)

    def send_email(self, message: str) -> bool:
        """
        Sends an email notification using MIME format.
        
        Args:
            message: Email content
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.SENDER_EMAIL
            msg['To'] = self.config.RECIPIENT_EMAIL
            msg['Subject'] = "New Posts Found on Snipers Hide Forum"
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(self.config.SENDER_EMAIL, self.config.SENDER_PASSWORD)
                smtp.send_message(msg)
                
            logging.info("Email sent successfully!")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return False

    def check_forum(self) -> None:
        """
        Main function to check forum for new posts.
        """
        logging.info("Starting forum check...")
        all_posts = []
        current_time = datetime.now(timezone.utc)
        
        for link_config in self.config.SEARCH_LINKS:
            soup = self.get_page_content(link_config["url"])
            if not soup:
                continue
                
            recent_posts = []
            posts = soup.find_all("h3", class_="contentRow-title")
            
            for post in posts:
                try:
                    post_link = post.find("a")
                    if not post_link:
                        continue
                        
                    href = post_link.get("href", "")
                    post_title = post_link.get_text(strip=True)
                    
                    # Construct full URL
                    full_link = f"https://www.snipershide.com{href}" if href.startswith("/") else href
                    
                    time_tag = post.find_next("time", class_="u-dt")
                    if not time_tag or 'datetime' not in time_tag.attrs:
                        continue
                        
                    post_time = self.parse_post_time(time_tag['datetime'])
                    if not post_time:
                        continue
                        
                    # Check if post is within time window
                    if current_time - post_time <= timedelta(minutes=self.config.TIME_WINDOW_MINUTES):
                        recent_posts.append({
                            'title': post_title,
                            'link': full_link,
                            'time': post_time
                        })
                        
                except Exception as e:
                    logging.error(f"Error processing post: {str(e)}")
                    continue
            
            if recent_posts:
                formatted_section = self.format_post_data(recent_posts, link_config["title"])
                all_posts.append(formatted_section)
        
        if all_posts:
            message = "\n\n".join(all_posts)
            if not self.send_email(message):
                logging.error("Failed to send notification email")
        else:
            logging.info("No new posts found")

def main():
    try:
        monitor = ForumMonitor(config)
        monitor.check_forum()
    except Exception as e:
        logging.error(f"Main execution failed: {str(e)}")

if __name__ == "__main__":
    main()