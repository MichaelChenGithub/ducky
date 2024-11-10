import streamlit as st
import helpers.sidebar
import asyncio
import os
from services.images import generate_image, get_all_images, delete_image

st.set_page_config(
    page_title="Images",
    page_icon="🏞️",
    layout="wide"
)

helpers.sidebar.show()

st.header("Image Generation")

# Create tabs
tab1, tab2 = st.tabs(["Image Generation", "Image List"])

# Image Generation Tab
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create text input for prompt
        prompt = st.text_area(
            label="Prompt",
            placeholder="Enter a prompt for the image generation model",
            height=100
        )
        
        # Add generation options
        col_model, col_style, col_quality, col_size = st.columns(4)
        
        with col_model:
            model = st.selectbox(
                "Model",
                options=["dall-e-3"],
                index=0
            )
            
        with col_style:
            style = st.selectbox(
                "Style",
                options=["vivid", "natural"],
                index=0
            )
            
        with col_quality:
            quality = st.selectbox(
                "Quality",
                options=["hd", "standard"],
                index=0
            )
            
        with col_size:
            size = st.selectbox(
                "Size",
                options=["1024x1024", "1792x1024", "1024x1792"],
                index=0
            )
    
        # Create generate button
        if st.button("Generate Image", type="primary"):
            if prompt:
                try:
                    # Show loading message while generating
                    with st.spinner("Generating image..."):
                        # Create event loop for async operation
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # Call generate_image function
                        prompt_text, image_path = loop.run_until_complete(generate_image(
                            prompt=prompt,
                            model=model,
                            style=style,
                            quality=quality,
                            size=size
                        ))
                        loop.close()
                        
                        # Store the generated image path in session state
                        if not 'generated_images' in st.session_state:
                            st.session_state.generated_images = []
                        st.session_state.generated_images.append({
                            'path': image_path,
                            'prompt': prompt_text
                        })
                        
                        st.success("Image generated successfully!")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter a prompt before generating an image.")
    
    with col2:
        # Display the most recently generated image
        if 'generated_images' in st.session_state and st.session_state.generated_images:
            latest_image = st.session_state.generated_images[-1]
            st.image(latest_image['path'], caption=latest_image['prompt'], use_column_width=True)

# Image List Tab
with tab2:
    # Get all images
    df = get_all_images()
    
    if len(df) > 0:
        # Add search filter
        search_term = st.text_input("Search descriptions", "")
        
        # Filter based on search term
        if search_term:
            df = df[df['Description'].str.contains(search_term, case=False, na=False)]
        
        # Display images in a grid
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                # Create a container for each image
                with st.container():
                    st.image(row['Image'], use_column_width=True)
                    st.caption(f"Created: {row['Date Created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Create an expander for the description
                    with st.expander("Description"):
                        st.write(row['Description'])
                    
                    # Add delete button
                    if st.button(f"Delete", key=f"delete_{idx}"):
                        try:
                            delete_image(row['Image'])
                            st.success("Image deleted successfully!")
                            # Refresh the page
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting image: {str(e)}")
                    
                    st.divider()
    else:
        st.info("No images found. Generate some images in the 'Image Generation' tab!")

# Add CSS to improve the layout
st.markdown("""
    <style>
        .stButton button {
            width: 100%;
        }
        .element-container {
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)