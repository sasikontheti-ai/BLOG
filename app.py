import streamlit as st
import os
import time
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# for m in genai.list_models():
#     if "generateContent" in m.supported_generation_methods:
#         print(m.name)

# Setup API Key (better practice)
api_key = os.getenv("GOOGLE_API_KEY")
# For now you can also hardcode if needed:
# api_key = "YOUR_API_KEY"

# Configure API
genai.configure(api_key=api_key)

# Get available models
available_models = []
try:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            available_models.append(m.name)
except Exception as e:
    st.sidebar.error(f"Error listing models: {e}")

# Sidebar for model selection
st.sidebar.header("⚙️ Configuration")
selected_model_name = st.sidebar.selectbox(
    "Select Model", 
    available_models, 
    index=0 if available_models else None
)

# Function to get Gemini response
def get_gemini_response(input_text, image, prompt):
    if not selected_model_name:
        return "Error: No model selected."
        
    model = genai.GenerativeModel(selected_model_name)
    
    # Retry logic for handling quota exhaustion
    retry_delay = 10  # Start with 10 seconds
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content([input_text, image[0], prompt])
            return response.text
        except Exception as e:
            # Check for quota/rate limit errors
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg or "resource_exhausted" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Double the delay for the next attempt
                    continue
            # If not a quota error or out of retries, re-raise
            raise e

# Function to setup input image


def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()

        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")


# Initialize Streamlit app
st.set_page_config(
    page_title="Gemini Historical Artifact Description App", page_icon="🏺")

st.header("🏺 Gemini Historical Artifact Description App")

input_text = st.text_input("📝 Input Prompt: ", key="input")

uploaded_file = st.file_uploader(
    "🖼️ Choose an image of an artifact...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="📷 Uploaded Image.", width=500)  # ✅ Fixed

submit = st.button("🚀 Generate Artifact Description")

input_prompt = """
You are a historian. Please describe the historical artifact in the image 
and provide detailed information, including its name, origin, time period, 
and significance.
"""

# If submit button is clicked
if submit:
    try:
        image_data = input_image_setup(uploaded_file)
        with st.spinner("Analyzing the artifact..."):
            response = get_gemini_response(input_text, image_data, input_prompt)
            st.subheader("📜 Description of the Artifact:")
            st.write(response)
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")