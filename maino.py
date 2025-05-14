import datetime
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import json
import os
from io import BytesIO
from datetime import datetime
from skimage.util import random_noise
from streamlit_image_comparison import image_comparison
import matplotlib.pyplot as plt
import time

# USER MANAGEMENT FUNCTIONS

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def authenticate(email, password):
    users = st.session_state.users
    return email in users and users[email]["password"] == password

def calculate_age(dob):
    today = datetime.now()
    dob_date = datetime.strptime(dob, "%Y-%m-%d")
    return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

def register_user(first_name, last_name, dob, email, password):
    if email in st.session_state.users:
        return False
    
    st.session_state.users[email] = {
        "first_name": first_name,
        "last_name": last_name,
        "dob": str(dob),
        "password": password,
        "enhancement_count": 0,
        "enhancement_types": [],
        "enhancement_history": [],
        "join_date": datetime.now().strftime("%Y-%m-%d")
    }
    save_users(st.session_state.users)
    return True


# IMAGE PROCESSING FUNCTIONS

def apply_histogram_equalization(image):
    if len(image.shape) == 2:
        equalized = cv2.equalizeHist(image)
        return cv2.cvtColor(equalized, cv2.COLOR_GRAY2RGB)
    else:
        img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
        return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)

def apply_gaussian_blur(image):
    return cv2.GaussianBlur(image, (5, 5), 0)

def apply_sharpening(image):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)

def apply_edge_detection(image):
    edges = cv2.Canny(image, 100, 200)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

def apply_complement(image):
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    complement = cv2.bitwise_not(img_gray)
    return cv2.cvtColor(complement, cv2.COLOR_GRAY2RGB)

def apply_salt_and_pepper(image):
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    noisy = random_noise(img_gray, mode='s&p', amount=0.05)
    noisy = np.array(255 * noisy, dtype='uint8')
    return cv2.cvtColor(noisy, cv2.COLOR_GRAY2RGB)

def apply_denoise(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

def image_to_bytes(image, format):
    buf = BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()


# SESSION STATE INITIALIZATION

if "users" not in st.session_state:
    st.session_state.users = load_users()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "enhanced_image" not in st.session_state:
    st.session_state.enhanced_image = None
if "original_image" not in st.session_state:
    st.session_state.original_image = None
if "tab_selection" not in st.session_state:
    st.session_state.tab_selection = "Enhancement"
if "show_success" not in st.session_state:
    st.session_state.show_success = False




# SIDEBAR NAVIGATION - MODERN DESIGN

with st.sidebar:
    if not st.session_state.authenticated:
        st.markdown("""
        <div class="custom-card">
            <h3>🔑 Authentication</h3>
        """, unsafe_allow_html=True)
        
        auth_choice = st.radio("", ["Login", "Register"], label_visibility="collapsed")
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        user_data = st.session_state.users.get(st.session_state.current_user, {})
        st.markdown(f"""
        <div class="custom-card">
            <div style="text-align: center;">
                <img src="https://ui-avatars.com/api/?name={user_data.get('first_name','')}+{user_data.get('last_name','')}&background=1976d2&color=fff&size=100" 
                     style="border-radius: 50%; border: 3px solid #1976d2; margin-bottom: 1rem;">
                <h4>{user_data.get('first_name','')} {user_data.get('last_name','')}</h4>
                <p style="color: #546e7a; font-size: 0.9rem;">{st.session_state.current_user}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.tab_selection = st.radio(
            "Navigation",
            ["Enhancement", "My Profile", "Charts"],
            label_visibility="visible"
        )
        
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.original_image = None
            st.session_state.enhanced_image = None
            st.session_state.tab_selection = "Enhancement"
            st.success("Logged out successfully!")
            time.sleep(1)
            st.rerun()


# AUTHENTICATION PAGES - MODERN FORMS

if not st.session_state.authenticated:
    if auth_choice == "Register":
        with st.container():
            st.markdown("""
            <div class="custom-card animate-fade">
                <h2>📝 Create Account</h2>
                <p style="color: #546e7a;">Join our platform to unlock professional image enhancements</p>
            """, unsafe_allow_html=True)
            
            with st.form("register_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name", placeholder="John")
                with col2:
                    last_name = st.text_input("Last Name", placeholder="Doe")
                
                dob = st.date_input("Date of Birth", 
                                  max_value=datetime.now(), 
                                  min_value=datetime(1925, 1, 1),
                                  value=datetime(1990, 1, 1))
                
                email = st.text_input("Email Address", placeholder="your.email@example.com")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if not all([first_name, last_name, dob, email, password, confirm_password]):
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif email in st.session_state.users:
                    st.error("Email already registered")
                else:
                    if register_user(first_name, last_name, dob, email, password):
                        st.success("Account created successfully! Please log in.")
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif auth_choice == "Login":
        with st.container():
            st.markdown("""
            <div class="custom-card animate-fade">
                <h2>🔐 Welcome Back</h2>
                <p style="color: #546e7a;">Sign in to access your image enhancements</p>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="your.email@example.com")
                password = st.text_input("Password", type="password")
                
                login_submitted = st.form_submit_button("Sign In")
            
            if login_submitted:
                if authenticate(email, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = email
                    st.session_state.show_success = True
                    st.success("Login successful!")
                    st.snow()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            
            st.markdown("</div>", unsafe_allow_html=True)


# MAIN APPLICATION PAGES

else:
    user_data = st.session_state.users.get(st.session_state.current_user, {})
    
    # ENHANCEMENT TAB
    if st.session_state.tab_selection == "Enhancement":
        with st.container():
            st.markdown("""
            <div class="custom-card animate-fade">
                <h2>✨ Image Enhancement</h2>
                <p style="color: #546e7a;">Upload your image and apply professional enhancements</p>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Choose an image file", 
                type=["jpg", "jpeg", "png", "bmp", "tiff"],
                label_visibility="collapsed"
            )
            
            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    image_np = np.array(image.convert("RGB"))
                    st.session_state.original_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                    
                    st.image(image, caption="Original Image", use_column_width=True)
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
            
            if st.session_state.original_image is not None:
                enhancement_option = st.selectbox(
                    "Select Enhancement Type",
                    [
                        "Histogram Equalization (Contrast)",
                        "Gaussian Blur (Smoothing)",
                        "Sharpening (Detail Enhancement)",
                        "Edge Detection (Feature Extraction)",
                        "Complement (Invert Colors)",
                        "Salt & Pepper Noise (Film Grain)",
                        "Denoise (Noise Reduction)"
                    ],
                    index=0
                )
                
                if st.button("Apply Enhancement", key="enhance_btn"):
                    with st.spinner("Processing image..."):
                        try:
                            img = st.session_state.original_image
                            if "Histogram" in enhancement_option: 
                                result = apply_histogram_equalization(img)
                            elif "Gaussian" in enhancement_option: 
                                result = apply_gaussian_blur(img)
                            elif "Sharpening" in enhancement_option: 
                                result = apply_sharpening(img)
                            elif "Edge" in enhancement_option: 
                                result = apply_edge_detection(img)
                            elif "Complement" in enhancement_option: 
                                result = apply_complement(img)
                            elif "Salt" in enhancement_option: 
                                result = apply_salt_and_pepper(img)
                            elif "Denoise" in enhancement_option: 
                                result = apply_denoise(img)
                            
                            st.session_state.enhanced_image = result
                            
                            # Update user stats
                            user_data["enhancement_count"] += 1
                            tech_name = enhancement_option.split(" ")[0]
                            if tech_name not in user_data["enhancement_types"]:
                                user_data["enhancement_types"].append(tech_name)
                            user_data["enhancement_history"].append({
                                "technique": tech_name,
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "filename": uploaded_file.name if uploaded_file else "unknown"
                            })
                            save_users(st.session_state.users)
                            
                            st.success("Enhancement applied successfully!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error during enhancement: {str(e)}")
            
            if st.session_state.enhanced_image is not None:
                original_rgb = cv2.cvtColor(st.session_state.original_image, cv2.COLOR_BGR2RGB)
                enhanced_rgb = cv2.cvtColor(st.session_state.enhanced_image, cv2.COLOR_BGR2RGB)
                
                st.markdown("### Comparison Viewer")
                image_comparison(
                    img1=original_rgb, 
                    img2=enhanced_rgb, 
                    label1="Original", 
                    label2="Enhanced",
                    width=700,
                    starting_position=50
                )
                
                st.markdown("### Download Options")
                download_format = st.selectbox(
                    "Select format",
                    ["PNG", "JPEG", "WebP"],
                    index=0,
                    key="download_format"
                )
                
                if download_format == "PNG":
                    dl_btn = st.download_button(
                        "Download PNG",
                        data=image_to_bytes(Image.fromarray(enhanced_rgb), 'PNG'),
                        file_name="enhanced.png",
                        mime="image/png"
                    )
                elif download_format == "JPEG":
                    dl_btn = st.download_button(
                        "Download JPEG",
                        data=image_to_bytes(Image.fromarray(enhanced_rgb), 'JPEG'),
                        file_name="enhanced.jpg",
                        mime="image/jpeg"
                    )
                elif download_format == "WebP":
                    dl_btn = st.download_button(
                        "Download WebP",
                        data=image_to_bytes(Image.fromarray(enhanced_rgb), 'WEBP'),
                        file_name="enhanced.webp",
                        mime="image/webp"
                    )
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # PROFILE TAB
    elif st.session_state.tab_selection == "My Profile":
        with st.container():
            st.markdown("""
            <div class="custom-card animate-fade">
                <h2>👤 User Profile</h2>
                <p style="color: #546e7a;">Your account information and statistics</p>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"""
                <div style="text-align: center;">
                    <img src="https://ui-avatars.com/api/?name={user_data.get('first_name','')}+{user_data.get('last_name','')}&background=1976d2&color=fff&size=150" 
                         style="border-radius: 50%; border: 3px solid #1976d2; margin-bottom: 1rem;">
                    <h3>{user_data.get('first_name','')} {user_data.get('last_name','')}</h3>
                    <p style="color: #546e7a;">Member since {user_data.get('join_date','')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### Account Details")
                st.markdown(f"""
                - **Email:** {st.session_state.current_user}
                - **Date of Birth:** {user_data.get('dob','')}
                - **Age:** {calculate_age(user_data.get('dob',''))}
                - **Total Enhancements:** {user_data.get('enhancement_count',0)}
                - **Techniques Used:** {', '.join(user_data.get('enhancement_types',[])) or 'None'}
                """)
                
                st.markdown("### Recent Activity")
                if user_data.get("enhancement_history"):
                    for i, activity in enumerate(reversed(user_data["enhancement_history"][-5:])):
                        st.markdown(f"""
                        <div style="background: #f5f7fa; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong>{activity['technique']}</strong>
                                <span style="color: #546e7a; font-size: 0.85rem;">{activity['date']}</span>
                            </div>
                            <div style="color: #546e7a; font-size: 0.9rem;">{activity.get('filename','')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No enhancement history yet")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # CHARTS TAB
    elif st.session_state.tab_selection == "Charts":
        with st.container():
            st.markdown("""
            <div class="custom-card animate-fade">
                <h2>📊 Enhancement Analytics</h2>
                <p style="color: #546e7a;">Visualize your enhancement patterns</p>
            """, unsafe_allow_html=True)
            
            if user_data.get("enhancement_count", 0) > 0:
                # Enhancement type distribution
                enhancement_types = [h["technique"] for h in user_data.get("enhancement_history", [])]
                if enhancement_types:
                    type_counts = {t: enhancement_types.count(t) for t in set(enhancement_types)}
                    
                    st.markdown("### Technique Usage")
                    fig1, ax1 = plt.subplots(figsize=(8, 4))
                    ax1.bar(type_counts.keys(), type_counts.values(), color='#1976d2')
                    ax1.set_title('Enhancement Techniques Used')
                    ax1.set_ylabel('Count')
                    plt.xticks(rotation=45)
                    st.pyplot(fig1)
                    
                    # Timeline visualization
                    st.markdown("### Activity Timeline")
                    dates = [datetime.strptime(h["date"], "%Y-%m-%d %H:%M:%S") for h in user_data["enhancement_history"]]
                    dates.sort()
                    
                    fig2, ax2 = plt.subplots(figsize=(8, 4))
                    ax2.plot(dates, range(1, len(dates)+1), marker='o', color='#e53935')
                    ax2.set_title('Enhancement Activity Over Time')
                    ax2.set_ylabel('Total Enhancements')
                    plt.xticks(rotation=45)
                    st.pyplot(fig2)
            else:
                st.info("No enhancement data available yet. Process some images to see analytics.")
            
            st.markdown("</div>", unsafe_allow_html=True)


st.markdown("""
<div style="text-align: center; color: #546e7a; margin-top: 3rem;">
    <hr style="border: 0.5px solid #cfd8dc;">
    <p>Image Enhancement Pro • {year}</p>
</div>
""".format(year=datetime.now().year), unsafe_allow_html=True)