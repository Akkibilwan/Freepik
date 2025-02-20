import streamlit as st
import requests
import json
import googleapiclient.discovery

# Load API keys from Streamlit secrets
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
FREEPIK_API_KEY = st.secrets["FREEPIK_API_KEY"]

# YouTube API setup
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Freepik API endpoint
FREEPIK_API_URL = "https://api.freepik.com/v1/resources"

# Initialize YouTube API client
youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

# Initialize session state for selected video
if "selected_video" not in st.session_state:
    st.session_state["selected_video"] = None

# Function to get YouTube videos based on search query
def search_youtube_videos(query, max_results=10):
    request = youtube.search().list(
        q=query,
        part="snippet",
        maxResults=max_results,
        type="video"
    )
    response = request.execute()
    
    video_data = []
    
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        thumbnail_url = item["snippet"]["thumbnails"]["medium"]["url"]
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]
        
        # Get video statistics (views)
        stats_request = youtube.videos().list(
            id=video_id,
            part="statistics"
        )
        stats_response = stats_request.execute()
        
        views = int(stats_response["items"][0]["statistics"].get("viewCount", 0))
        
        # Get channel average views
        avg_views = get_channel_avg_views(channel_id)
        
        # Calculate outlier score
        outlier_score = round(views / avg_views, 2) if avg_views > 0 else 1.0

        video_data.append({
            "title": title,
            "video_id": video_id,
            "thumbnail_url": thumbnail_url,
            "channel_title": channel_title,
            "views": views,
            "outlier_score": outlier_score
        })
    
    return sorted(video_data, key=lambda x: x["outlier_score"], reverse=True)

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

# Function to get similar images using Freepik API
def get_freepik_images(query, model, num_results=3):
    headers = {"Authorization": f"Bearer {FREEPIK_API_KEY}"}
    params = {"query": query, "type": "photo", "model": model, "page": 1, "limit": num_results}
    
    response = requests.get(FREEPIK_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        return None

# Streamlit UI
st.title("🔍 YouTube & Freepik Search App")

# User inputs
query = st.text_input("Enter a keyword to search YouTube videos:")
max_results = st.number_input("Number of results (1-15):", min_value=1, max_value=15, value=5)

if st.button("Search YouTube"):
    if query:
        video_results = search_youtube_videos(query, max_results)
        
        if video_results:
            st.write(f"Showing results for: **{query}**")
            cols = st.columns(3)  # Create a 3-column layout
            
            for index, video in enumerate(video_results):
                with cols[index % 3]:  # Display thumbnails in a grid
                    st.image(video["thumbnail_url"], caption=f"{video['title']} ({video['views']} views, Outlier: {video['outlier_score']}x)", use_column_width=True)
                    if st.button(f"Select {index+1}", key=f"video_{index}"):
                        st.session_state["selected_video"] = video  # Store selected video in session state
            
# Check if a video is selected
if st.session_state["selected_video"]:
    selected_video = st.session_state["selected_video"]
    st.write("### 🎨 Generate Similar Image from Freepik")
    st.write(f"Selected video: **{selected_video['title']}**")
    
    # Choose Freepik AI Model
    model_choice = st.selectbox("Select Freepik Model:", ["classic-fast", "mystic"])
    num_images = st.number_input("Number of images (1-5):", min_value=1, max_value=5, value=3)
    
    if st.button("Generate Freepik Images"):
        images = get_freepik_images(selected_video["title"], model_choice, num_images)
        
        if images:
            st.write("### 🖼️ Freepik Generated Images")
            img_cols = st.columns(3)
            for i, img in enumerate(images):
                with img_cols[i % 3]:
                    st.image(img["url"], caption=f"Generated Image {i+1}", use_column_width=True)
        else:
            st.error("No images found! Try a different model or keyword.")
