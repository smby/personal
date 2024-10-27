import requests
from bs4 import BeautifulSoup
import smtplib
import time
import schedule
import config  # Import configuration file

# URL for searching posts
search_url = "https://www.snipershide.com/shooting/search/7199250/?q=amp+annealer&c[newer_than]=2024-10-01&c[title_only]=1&o=date"

# Store previously found posts to avoid duplicate emails
last_checked_posts = set()

def check_forum():
    """Checks the forum for new posts related to 'AMP annealer'."""
    global last_checked_posts
    print("Checking the forum for new posts...")

    # First GET request to open the page and trigger any required confirmation
    requests.get(search_url)
    time.sleep(1)  # Short delay to mimic user interaction

    # Second GET request to simulate pressing "Enter" and bypassing the age gate
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract post information based on the updated structure
    posts = soup.find_all("h3", class_="contentRow-title")
    print(f"Number of posts found with 'contentRow-title' class: {len(posts)}")  # Debug print statement

    new_posts = []
    for post in posts:
        post_link = post.find("a")["href"]  # Get the href link from the <a> tag within <h3>
        post_title = post.get_text(strip=True)
        print(f"Found post: {post_title}")  # Debug print statement

        # Add the base URL if necessary to form a full URL
        full_link = f"https://www.snipershide.com{post_link}" if post_link.startswith("/") else post_link

        if full_link not in last_checked_posts:
            last_checked_posts.add(full_link)
            new_posts.append(f"{post_title}: {full_link}")

    # If there are new posts, send an email
    if new_posts:
        print("New posts found, sending email...")
        send_email("\n".join(new_posts))
    else:
        print("No new posts found.")

def send_email(message):
    """Sends an email notification."""
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            subject = "New AMP Annealer Post on Snipers Hide"
            body = f"Subject: {subject}\n\n{message}"
            email_message = f"Subject: {subject}\n\n{body}"
            smtp.sendmail(config.SENDER_EMAIL, config.RECIPIENT_EMAIL, email_message)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Main function to handle scheduling
def main():
    schedule.every(1).minutes.do(check_forum)  # Set to 1-minute intervals for testing
    print("Script started, waiting to run scheduled checks...")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()