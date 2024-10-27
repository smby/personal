import requests
from bs4 import BeautifulSoup
import smtplib
from datetime import datetime, timedelta
import config  # Import configuration file

# URL for searching posts
search_url = "https://www.snipershide.com/shooting/search/7199250/?q=amp+annealer&c[newer_than]=2024-10-01&c[title_only]=1&o=date"

# Define the time window (in minutes) to consider posts as "new"
TIME_WINDOW_MINUTES = 60

def log_message(message):
    """Logs a message with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def check_forum():
    """Checks the forum for new posts created within the defined time window."""
    log_message("Checking the forum for new posts...")

    # First GET request to open the page and trigger any required confirmation
    requests.get(search_url)
    # Short delay to mimic user interaction
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Get the current time with timezone for comparison
    current_time = datetime.now().astimezone()

    # List to hold new posts within the time window
    recent_posts = []

    # Find all post titles and their corresponding timestamps
    posts = soup.find_all("h3", class_="contentRow-title")
    for post in posts:
        post_link = post.find("a")["href"]
        post_title = post.get_text(strip=True)
        full_link = f"https://www.snipershide.com{post_link}" if post_link.startswith("/") else post_link

        # Locate the timestamp of the post
        time_tag = post.find_next("time", class_="u-dt")
        if time_tag and 'datetime' in time_tag.attrs:
            post_time = datetime.fromisoformat(time_tag['datetime'])

            # Check if the post was created within the defined time window
            if current_time - post_time <= timedelta(minutes=TIME_WINDOW_MINUTES):
                recent_posts.append(f"{post_title} (Created at {post_time.strftime('%Y-%m-%d %H:%M:%S')}): {full_link}")

    # If there are recent posts, send an email
    if recent_posts:
        log_message("New posts found, sending email...")
        send_email("\n".join(recent_posts))
    else:
        log_message("No new posts found.")

def send_email(message):
    """Sends an email notification."""
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            subject = "New AMP Annealer Post on Snipers Hide"
            body = f"Subject: {subject}\n\n{message}"
            smtp.sendmail(config.SENDER_EMAIL, config.RECIPIENT_EMAIL, body)
            log_message("Email sent successfully!")
    except Exception as e:
        log_message(f"Failed to send email: {e}")

if __name__ == "__main__":
    check_forum()

