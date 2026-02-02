import streamlit as st
import pandas as pd
from passlib.context import CryptContext
import json
from .database_setup import get_connection
import base64
import random
from datetime import date

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

MCQ_QUESTIONS = [
    "What was the name of your first pet?",
    "What is the city where you were born?",
    "What is your mother's maiden name?",
    "What was the make of your first car?",
    "What is your favorite food?",
    "What is the name of your elementary school?",
    "What is your favorite movie?",
    "What is your father's middle name?"
]

SHORT_QUESTIONS = [
    "What is your nick name?",
    "Who is your favorite teacher?",
    "What is your dream job?",
    "What is your favorite color?",
    "What is your favorite sport?",
    "Who is your childhood hero?"
]

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def generate_user_id(name):
    # Logic: Name-Number (e.g. Manoj-005)
    conn = get_connection()
    c = conn.cursor()
    
    first_name = name.split()[0].capitalize()
    
    # Count existing users to append a number
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0] + 1
    
    user_id = f"{first_name}-{count:03d}" 
    
    # Ensure uniqueness
    while True:
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not c.fetchone():
            break
        count += 1
        user_id = f"{first_name}-{count:03d}"
        
    conn.close()
    return user_id

def register_user(name, username, email, mobile, dob, pin, security_data):
    conn = get_connection()
    c = conn.cursor()
    
    # Check username/email uniqueness
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already taken.", None
        
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "Email already registered.", None

    user_id = generate_user_id(name)
    pin_hash = hash_password(pin)
    security_questions_json = json.dumps(security_data)
    
    c.execute('''
        INSERT INTO users (username, name, email, mobile_number, dob, pin_hash, security_questions, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, name, email, mobile, str(dob), pin_hash, security_questions_json, user_id))
    
    conn.commit()
    conn.close()
    return True, f"Registration Successful! Your User ID is: {user_id}", user_id

def authenticate_user(identifier, pin):
    conn = get_connection()
    c = conn.cursor()
    
    # Allow login with either username or user_id
    c.execute("SELECT pin_hash, username FROM users WHERE username = ? OR user_id = ?", (identifier, identifier))
    result = c.fetchone()
    conn.close()
    
    if result and verify_password(pin, result[0]):
        return True, result[1] # Return real username for session
    return False, None

def get_security_questions(identifier):
    # Identifier can be user_id or email or username
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT security_questions, user_id, username FROM users WHERE user_id = ? OR email = ? OR username = ?", (identifier, identifier, identifier))
    result = c.fetchone()
    conn.close()
    
    if result:
        return json.loads(result[0]), result[1], result[2]
    return None, None, None

def reset_pin(username, new_pin):
    conn = get_connection()
    c = conn.cursor()
    pin_hash = hash_password(new_pin)
    c.execute("UPDATE users SET pin_hash = ? WHERE username = ?", (pin_hash, username))
    conn.commit()
    conn.close()
    return True

def change_pin(username, old_pin, new_pin):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT pin_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if not result or not verify_password(old_pin, result[0]):
        conn.close()
        return False, "Old PIN is incorrect."
    
    new_hash = hash_password(new_pin)
    c.execute("UPDATE users SET pin_hash = ? WHERE username = ?", (new_hash, username))
    conn.commit()
    conn.close()
    return True, "PIN changed successfully!"

def update_user_setting(username, key, value):
    conn = get_connection()
    c = conn.cursor()
    if key not in ['hue', 'language']: return False
    query = f"UPDATE users SET {key} = ? WHERE username = ?"
    c.execute(query, (value, username))
    conn.commit()
    conn.close()
    return True

def get_user_settings(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT hue, language FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return {"hue": result[0], "language": result[1]}
    return {"hue": 0, "language": "en"}

def render_auth():
    # Centered Vertical Layout
    logo_b64 = get_base64_image("assets/icon-192x192.png")
    logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style='text-align: center;'>
            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px;'>
                <img src='{logo_src}' style='width: 80px; height: 80px; border-radius: 20px; box-shadow: 0 8px 30px rgba(255, 64, 129, 0.4); margin-bottom: 15px;'>
                <h1 style='font-size: 3rem; margin: 0; background: linear-gradient(to right, #ff4081, #ff80ab); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>mahwari</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Sign In", "Sign Up", "Forgot PIN"])
        
        with tab1:
            st.markdown("<h3 style='text-align: center;'>Welcome Back</h3>", unsafe_allow_html=True)
            login_id = st.text_input("Username or User ID", key="login_id", placeholder="e.g. priya or Priya-001")
            login_pin = st.text_input("6-Digit PIN", type="password", max_chars=6, key="login_pin", placeholder="• • • • • •")
            
            if st.button("Unlock", key="btn_login", use_container_width=True):
                success, real_username = authenticate_user(login_id, login_pin)
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = real_username
                    st.success("Sign In Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Username/ID or PIN")

        with tab2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)
            
            # Initialize random questions in session state
            if "signup_mcq" not in st.session_state:
                st.session_state["signup_mcq"] = random.sample(MCQ_QUESTIONS, 3)
                st.session_state["signup_short"] = random.sample(SHORT_QUESTIONS, 3)
            
            with st.form("signup_form"):
                new_name = st.text_input("Full Name")
                new_username = st.text_input("Username (for Sign In)")
                new_mobile = st.text_input("Mobile Number")
                new_email = st.text_input("Email")
                min_date = date(1990, 1, 1)
                max_date = date.today()
                new_dob = st.date_input("Date of Birth", min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
                
                new_pin = st.text_input("Create 6-Digit PIN", type="password", max_chars=6, help="Memorize this!")
                
                st.markdown("### Security Questions")
                st.info("Please answer the following questions for account recovery.")
                
                q_mcq = st.session_state["signup_mcq"]
                q_short = st.session_state["signup_short"]
                
                # Q1-3 (Selectable)
                sq1 = st.selectbox("Select Question 1", q_mcq, index=0)
                sa1 = st.text_input("Answer 1")
                
                sq2 = st.selectbox("Select Question 2", q_mcq, index=1)
                sa2 = st.text_input("Answer 2")
                
                sq3 = st.selectbox("Select Question 3", q_mcq, index=2)
                sa3 = st.text_input("Answer 3")
                
                # Q4-6 (Fixed Short Answer)
                st.markdown("---")
                sq4 = q_short[0]
                st.write(f"4. {sq4}")
                sa4 = st.text_input("Answer 4")
                
                sq5 = q_short[1]
                st.write(f"5. {sq5}")
                sa5 = st.text_input("Answer 5")
                
                sq6 = q_short[2]
                st.write(f"6. {sq6}")
                sa6 = st.text_input("Answer 6")

                submitted = st.form_submit_button("Sign Up", use_container_width=True)
                
                if submitted:
                    if len(new_pin) < 6:
                        st.error("PIN must be 6 digits.")
                    elif not new_username:
                        st.error("Username is required")
                    else:
                        # Collect all 6
                        security_data = {
                            "q1": sq1, "a1": sa1,
                            "q2": sq2, "a2": sa2,
                            "q3": sq3, "a3": sa3,
                            "q4": sq4, "a4": sa4,
                            "q5": sq5, "a5": sa5,
                            "q6": sq6, "a6": sa6,
                        }
                        success, msg, uid = register_user(new_name, new_username, new_email, new_mobile, new_dob, new_pin, security_data)
                        if success:
                            st.success(msg)
                            st.balloons()
                            st.info(f"IMPORTANT: Your User ID is **{uid}**. Please save it!")
                            # Reset random questions for next user
                            del st.session_state["signup_mcq"]
                        else:
                            st.error(msg)
        
        # No outer closing div needed now


        # Recover PIN Tab separate or inside? User asked for "signin signup", usually combined.
        # But putting the closing div after tab2 means tab3 is OUTSIDE.
        # Wait, the structure in replacement must match.
        # Original code had tab3. I should include tab3 in the glass card too.

        with tab3:
            st.markdown("<h3 style='text-align: center;'>Recover PIN</h3>", unsafe_allow_html=True)
            forgot_input = st.text_input("Enter Username, User ID, or Email")
            if st.button("Find User", use_container_width=True):
                questions, found_uid, found_uname = get_security_questions(forgot_input)
                if questions:
                    st.session_state["recovery_questions"] = questions
                    st.session_state["recovery_uid"] = found_uid
                    st.session_state["recovery_uname"] = found_uname
                else:
                    st.error("User not found.")
            
            if "recovery_questions" in st.session_state:
                q_data = st.session_state["recovery_questions"]
                with st.form("recovery_form"):
                    st.write("Please answer the security questions:")
                    
                    # Ask in specific order stored
                    st.write(f"1. {q_data['q1']}")
                    ra1 = st.text_input("Answer 1", key="r_a1")
                    
                    st.write(f"2. {q_data['q2']}")
                    ra2 = st.text_input("Answer 2", key="r_a2")
                    
                    st.write(f"3. {q_data['q3']}")
                    ra3 = st.text_input("Answer 3", key="r_a3")
                    
                    st.write(f"4. {q_data['q4']}")
                    ra4 = st.text_input("Answer 4", key="r_a4")
                    
                    st.write(f"5. {q_data['q5']}")
                    ra5 = st.text_input("Answer 5", key="r_a5")
                    
                    st.write(f"6. {q_data['q6']}")
                    ra6 = st.text_input("Answer 6", key="r_a6")
                    
                    new_pin_reset = st.text_input("New 6-Digit PIN", type="password", max_chars=6)
                    
                    if st.form_submit_button("Reset PIN", use_container_width=True):
                        # Counting correct answers
                        correct_count = 0
                        if ra1 == q_data['a1']: correct_count += 1
                        if ra2 == q_data['a2']: correct_count += 1
                        if ra3 == q_data['a3']: correct_count += 1
                        if ra4 == q_data['a4']: correct_count += 1
                        if ra5 == q_data['a5']: correct_count += 1
                        if ra6 == q_data['a6']: correct_count += 1
                        
                        if correct_count >= 5:
                            reset_pin(st.session_state["recovery_uname"], new_pin_reset)
                            st.success("PIN Reset Successful!")
                            st.info(f"Your User ID is: **{st.session_state['recovery_uid']}**")
                            del st.session_state["recovery_questions"]
                        else:
                            st.error(f"Only {correct_count}/6 correct. You need at least 5 correct answers.")

