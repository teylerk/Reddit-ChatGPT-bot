import praw
import requests
import time
import re
from praw.exceptions import RedditAPIException

# Set up the Reddit API client
reddit = praw.Reddit(
    client_id="Reddit Client ID",
    client_secret="Reddit Secret",
    password="Reddit Password",
    user_agent="chatgpt", # No Need to change this 
    username="Reddit Username",
)

# Set up the ChatGPT API
chatgpt_url = "https://api.openai.com/v1/chat/completions"
chatgpt_api_key = "Enter OpenAI API Key Here" 
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {chatgpt_api_key}"}

def chatgpt_response(post_title, post_content):
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f"Act like you're a human and write a very short Reddit comment for the following Reddit post titled '{post_title}' and content: '{post_content}'"
            }
        ],
    }
    response = requests.post(chatgpt_url, headers=headers, json=data)
    response_text = response.json()["choices"][0]["message"]["content"].strip()
    response_text = response_text.replace('"', '')  # Remove quotes from the response
    return response_text


def process_comment(submission):
    post_title = submission.title
    post_content = submission.selftext  # Define post_content here
    response = chatgpt_response(post_title, post_content)

    try:
        submission.reply(response)
        print(f"Commented on submission with ID {submission.id}: {response}")
    except RedditAPIException as e:
        if "RATELIMIT" in str(e):
            wait_match = re.search(r"(\d+) (minutes?|seconds?)", str(e))
            wait_time = int(wait_match.group(1))
            wait_unit = wait_match.group(2)

            if wait_unit.startswith("minute"):
                wait_time *= 60
            elif wait_unit.startswith("second"):
                pass
            else:
                print(f"Unexpected rate limit time unit: {wait_unit}. Defaulting to seconds.")
                
            print(f"Rate limit exceeded. Waiting for {wait_time} {wait_unit}.")
            time.sleep(wait_time)
            process_comment(submission)
        elif "TOO_OLD" in str(e):
            print(f"Submission {submission.id} is too old to reply to.")
        else:
            print(f"Error processing comment {submission.id}: {e}")


processed_submissions = set()


def post_on_new_posts(subreddits):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        new_post = next(subreddit.new(limit=1))
        if new_post.id not in processed_submissions:
            process_comment(new_post)
            processed_submissions.add(new_post.id)
            time.sleep(60)  # Add a 60-second waiting time between posting new comments



def main():
    subreddits = ["Chatgpt", "news"] # Enter Subreddits Here 
    while True:
        try:
            post_on_new_posts(subreddits)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)  # Wait for 60 seconds before checking again

if __name__ == "__main__":
    main()
