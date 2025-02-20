import streamlit as st
import requests
import re

# Load API keys from Streamlit secrets
FREEPIK_API_KEY = st.secrets["FREEPIK_API_KEY"]

# Freepik API endpoint
FREEPIK_API_URL = "https://api.freepik.com/v1/resources"

# Function to extract YouTube video ID from URL
def extract_video_id(url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

# Function to get YouTube video thumbnail URL
def get_youtube_thumbnail(video_id):
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

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
st.title("🎥 YouTube Thumbnail Variation Generator (Freepik AI)")

# User input: YouTube video URL
video_url = st.text_input("Enter YouTube video URL:")

if video_url:
    # Extract video ID
    video_id = extract_video_id(video_url)
    
    if video_id:
        # Get thumbnail URL
        thumbnail_url = get_youtube_thumbnail(video_id)
        
        # Display original thumbnail
        st.write("### 🎬 Original YouTube Thumbnail")
        st.image(thumbnail_url, caption="Original Thumbnail", use_column_width=True)
        
        # Choose Freepik AI Model
        model_choice = st.selectbox("Select Freepik AI Model:", ["classic-fast", "mystic"])
        
        # Number of images to generate
        num_images = st.number_input("Number of images (1-5):", min_value=1, max_value=5, value=3)
        
        if st.button("Generate AI Variations"):
            images = get_freepik_images(video_id, model_choice, num_images)
            
            if images:
                st.write("### 🖼️ AI-Generated Variations")
                img_cols = st.columns(3)
                for i, img in enumerate(images):
                    with img_cols[i % 3]:
                        st.image(img["url"], caption=f"Variation {i+1}", use_column_width=True)
            else:
                st.error("No images found! Try a different model or keyword.")
    else:
        st.error("Invalid YouTube URL! Please enter a valid video link.")
