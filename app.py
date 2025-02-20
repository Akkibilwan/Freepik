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

# YouTube API setup
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Freepik API endpoint
FREEPIK_API_URL = "https://api.freepik.com/v1/resources"

# Initialize YouTube API client
youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

# Function to extract YouTube video ID from URL
def extract_video_id(url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

# Function to get YouTube video details (Title & Thumbnail)
def get_youtube_video_details(video_id):
    request = youtube.videos().list(
        id=video_id,
        part="snippet"
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        snippet = response["items"][0]["snippet"]
        return {
            "title": snippet["title"],
            "thumbnail_url": snippet["thumbnails"]["maxres"]["url"] if "maxres" in snippet["thumbnails"] else snippet["thumbnails"]["high"]["url"]
        }
    return None

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

# Function to get AI-generated variations from Freepik
def get_freepik_images(query, model, num_results=3):
    headers = {"Authorization": f"Bearer {FREEPIK_API_KEY}"}
    params = {"query": query, "type": "photo", "model": model, "page": 1, "limit": num_results}
    
    response = requests.get(FREEPIK_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        return None

# Streamlit UI
st.title("🎥 AI YouTube Thumbnail Variation Generator (OpenAI + Freepik)")

# User input: YouTube video URL
video_url = st.text_input("Enter YouTube video URL:")

if video_url:
    # Extract video ID
    video_id = extract_video_id(video_url)
    
    if video_id:
        # Get video details (Title & Thumbnail)
        video_details = get_youtube_video_details(video_id)
        
        if video_details:
            video_title = video_details["title"]
            thumbnail_url = video_details["thumbnail_url"]

            # Display original thumbnail
            st.write("### 🎬 Original YouTube Thumbnail")
            st.image(thumbnail_url, caption=f"Original Thumbnail - {video_title}", use_column_width=True)

            # Generate AI thumbnail prompt
            with st.spinner("Generating AI prompt for thumbnail..."):
                ai_prompt = generate_thumbnail_prompt(video_title)
            st.write(f"**📝 AI-Generated Prompt:** {ai_prompt}")

            # Choose Freepik AI Model
            model_choice = st.selectbox("Select Freepik AI Model:", ["classic-fast", "mystic"])
            
            # Number of images to generate
            num_images = st.number_input("Number of images (1-5):", min_value=1, max_value=5, value=3)
            
            if st.button("Generate AI Variations"):
                images = get_freepik_images(ai_prompt, model_choice, num_images)
                
                if images:
                    st.write("### 🖼️ AI-Generated Variations")
                    img_cols = st.columns(3)
                    for i, img in enumerate(images):
                        with img_cols[i % 3]:
                            st.image(img["url"], caption=f"Variation {i+1}", use_column_width=True)
                else:
                    st.error("No images found! Try a different model or keyword.")
        else:
            st.error("Unable to fetch video details. Please check the YouTube URL.")
    else:
        st.error("Invalid YouTube URL! Please enter a valid video link.")
