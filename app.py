import streamlit as st
import requests
import re
import googleapiclient.discovery
import openai

# Load API keys from Streamlit secrets
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
FREEPIK_API_KEY = st.secrets["FREEPIK_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Ensure API keys are provided
if not FREEPIK_API_KEY:
    st.error("❌ Freepik API Key is missing! Add it in `.streamlit/secrets.toml` or Streamlit Cloud settings.")
    st.stop()

# YouTube API setup
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Freepik API URL
FREEPIK_API_URL = "https://api.freepik.com/v1/resources"

# Initialize YouTube API client
youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

# Function to extract YouTube video ID from URL
def extract_video_id(url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

# Function to get YouTube video details
def get_youtube_video_details(video_id):
    request = youtube.videos().list(
        id=video_id,
        part="snippet,statistics"
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        snippet = response["items"][0]["snippet"]
        stats = response["items"][0].get("statistics", {})

        return {
            "title": snippet["title"],
            "thumbnail_url": snippet["thumbnails"]["maxres"]["url"] if "maxres" in snippet["thumbnails"] else snippet["thumbnails"]["high"]["url"],
            "channel_name": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "published_date": snippet["publishedAt"],
            "views": int(stats.get("viewCount", 0)),
            "likes": stats.get("likeCount", "N/A"),
            "comments": stats.get("commentCount", "N/A"),
        }
    return None

# Function to calculate average views of a channel
def get_channel_avg_views(channel_id):
    videos_request = youtube.search().list(
        channelId=channel_id,
        part="id",
        order="date",
        maxResults=10,
        type="video"
    )
    videos_response = videos_request.execute()

    total_views = 0
    video_count = 0

    for item in videos_response.get("items", []):
        video_id = item["id"]["videoId"]
        stats_request = youtube.videos().list(
            id=video_id,
            part="statistics"
        )
        stats_response = stats_request.execute()

        views = int(stats_response["items"][0]["statistics"].get("viewCount", 0))
        total_views += views
        video_count += 1

    return total_views / video_count if video_count > 0 else 0

# Function to generate a creative thumbnail prompt using OpenAI
def generate_thumbnail_prompt(video_title):
    prompt = f"Generate a creative, eye-catching thumbnail concept for a YouTube video titled: '{video_title}'. The image should be highly engaging, vibrant, and suitable for attracting viewers."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI that generates creative and engaging thumbnail descriptions for Freepik image generation."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

# Function to get AI-generated images from Freepik API
def get_freepik_images(query, model, num_results=3):
    headers = {
        "x-freepik-api-key": FREEPIK_API_KEY  # Correct header for API Key
    }
    params = {
        "query": query,
        "type": "photo",
        "model": model,
        "page": 1,
        "limit": num_results
    }

    response = requests.get(FREEPIK_API_URL, headers=headers, params=params)

    if response.status_code != 200:
        st.error(f"⚠️ Freepik API Error: {response.status_code} - {response.text}")
        return None

    return response.json().get("data", [])

# Streamlit UI
st.title("🎥 AI YouTube Thumbnail Generator (Stats + Outlier Score)")

# User input: YouTube video URL
video_url = st.text_input("Enter YouTube video URL:")

if video_url:
    video_id = extract_video_id(video_url)
    
    if video_id:
        video_details = get_youtube_video_details(video_id)
        
        if video_details:
            video_title = video_details["title"]
            thumbnail_url = video_details["thumbnail_url"]

            avg_views = get_channel_avg_views(video_details["channel_id"])
            outlier_score = round(video_details["views"] / avg_views, 2) if avg_views > 0 else 1.0

            st.write("### 🎬 Video Details")
            st.image(thumbnail_url, caption=f"Thumbnail - {video_title}", use_column_width=True)
            st.write(f"**📌 Title:** {video_details['title']}")
            st.write(f"**📺 Channel:** {video_details['channel_name']}")
            st.write(f"**👀 Views:** {video_details['views']} (Outlier Score: {outlier_score}x)")
            st.write(f"**👍 Likes:** {video_details['likes']}")
            st.write(f"**💬 Comments:** {video_details['comments']}")
            st.write(f"**📅 Published on:** {video_details['published_date']}")

            ai_prompt = generate_thumbnail_prompt(video_title)
            st.write("### ✨ AI-Generated Prompt")
            user_prompt = st.text_area("Modify the AI prompt before generating images:", ai_prompt)

            model_choice = st.selectbox("Select Freepik AI Model:", ["classic-fast", "mystic"])
            num_images = st.number_input("Number of images (1-5):", min_value=1, max_value=5, value=3)
            
            if st.button("Generate AI Variations"):
                images = get_freepik_images(user_prompt, model_choice, num_images)
                
                if images:
                    st.write("### 🖼️ AI-Generated Variations")
                    img_cols = st.columns(3)
                    for i, img in enumerate(images):
                        with img_cols[i % 3]:
                            st.image(img["url"], caption=f"Variation {i+1}", use_column_width=True)
                else:
                    st.error("No images found. Try modifying the prompt or model.")
        else:
            st.error("Unable to fetch video details. Please check the YouTube URL.")
