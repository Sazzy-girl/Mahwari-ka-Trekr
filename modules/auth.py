import streamlit as st
import pandas as pd
from passlib.context import CryptContext
import json
from .database_setup import get_connection

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECURITY_QUESTIONS_OPTIONS = [
    "What was the name of your first pet?",
    "What is the city where you were born?",
    "What is your mother's maiden name?",
    "What was the make of your first car?",
    "What is your favorite food?",
    "What is the name of your elementary school?"
]

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def register_user(name, username, email, dob, password, pin, security_answers):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already exists."
    
    password_hash = hash_password(password)
    pin_hash = hash_password(pin)
    security_questions_json = json.dumps(security_answers)
    
    c.execute('''
        INSERT INTO users (username, name, email, dob, password_hash, pin_hash, security_questions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, name, email, str(dob), password_hash, pin_hash, security_questions_json))
    
    conn.commit()
    conn.close()
    return True, "Registration successful! Please login."

def authenticate_user(username, pin):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT pin_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and verify_password(pin, result[0]):
        return True
    return False

def get_security_questions(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT security_questions FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return json.loads(result[0])
    return None

def reset_pin(username, new_pin):
    conn = get_connection()
    c = conn.cursor()
    pin_hash = hash_password(new_pin)
    c.execute("UPDATE users SET pin_hash = ? WHERE username = ?", (pin_hash, username))
    conn.commit()
    conn.close()
    return True

def render_auth():
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>Mahwari ka Trekr</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Forgot PIN"])
    
    with tab1:
        st.subheader("Login")
        login_user = st.text_input("Username", key="login_user")
        login_pin = st.text_input("6-Digit PIN", type="password", max_chars=6, key="login_pin")
        
        if st.button("Login", key="btn_login"):
            if authenticate_user(login_user, login_pin):
                st.session_state["authenticated"] = True
                st.session_state["username"] = login_user
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Username or PIN")

    with tab2:
        st.subheader("Create Account")
        with st.form("signup_form"):
            new_name = st.text_input("Full Name")
            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_dob = st.date_input("Date of Birth")
            new_pass = st.text_input("Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            new_pin = st.text_input("6-Digit PIN", type="password", max_chars=6, help="Memorize this!")
            
            st.markdown("### Security Questions")
            q1 = st.selectbox("Question 1", SECURITY_QUESTIONS_OPTIONS, index=0)
            a1 = st.text_input("Answer 1")
            q2 = st.selectbox("Question 2", SECURITY_QUESTIONS_OPTIONS, index=1)
            a2 = st.text_input("Answer 2")
            q3 = st.selectbox("Question 3", SECURITY_QUESTIONS_OPTIONS, index=2)
            a3 = st.text_input("Answer 3")
            
            st.markdown("### Additional Security")
            q4 = st.text_input("Custom Question 1")
            a4 = st.text_input("Answer 4")
            q5 = st.text_input("Custom Question 2")
            a5 = st.text_input("Answer 5")
            q6 = st.text_input("Custom Question 3")
            a6 = st.text_input("Answer 6")
            
            submitted = st.form_submit_button("Sign Up")
            
            if submitted:
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                elif len(new_pin) != 6:
                    st.error("PIN must be 6 digits.")
                else:
                    security_answers = {
                        "q1": q1, "a1": a1,
                        "q2": q2, "a2": a2,
                        "q3": q3, "a3": a3,
                        "q4": q4, "a4": a4,
                        "q5": q5, "a5": a5,
                        "q6": q6, "a6": a6
                    }
                    success, msg = register_user(new_name, new_user, new_email, new_dob, new_pass, new_pin, security_answers)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab3:
        st.subheader("Recover PIN")
        forgot_user = st.text_input("Enter Username to Recover")
        if st.button("Find User"):
            questions = get_security_questions(forgot_user)
            if questions:
                st.session_state["recovery_questions"] = questions
                st.session_state["recovery_user"] = forgot_user
            else:
                st.error("User not found.")
        
        if "recovery_questions" in st.session_state:
            q_data = st.session_state["recovery_questions"]
            with st.form("recovery_form"):
                st.write(f"1. {q_data['q1']}")
                ans1 = st.text_input("Answer 1", key="r_a1")
                st.write(f"2. {q_data['q2']}")
                ans2 = st.text_input("Answer 2", key="r_a2")
                st.write(f"3. {q_data['q3']}")
                ans3 = st.text_input("Answer 3", key="r_a3")
                st.write(f"4. {q_data['q4']}")
                ans4 = st.text_input("Answer 4", key="r_a4")
                st.write(f"5. {q_data['q5']}")
                ans5 = st.text_input("Answer 5", key="r_a5")
                st.write(f"6. {q_data['q6']}")
                ans6 = st.text_input("Answer 6", key="r_a6")
                
                new_pin_reset = st.text_input("New 6-Digit PIN", type="password", max_chars=6)
                
                if st.form_submit_button("Reset PIN"):
                    # Strict matching (case-sensitive or insensitive? Let's do exact match for now as per simple auth)
                    # For better UX, might want case-insensitive, but security-wise exact is safer.
                    if (ans1 == q_data['a1'] and ans2 == q_data['a2'] and 
                        ans3 == q_data['a3'] and ans4 == q_data['a4'] and 
                        ans5 == q_data['a5'] and ans6 == q_data['a6']):
                        
                        if len(new_pin_reset) == 6:
                            reset_pin(st.session_state["recovery_user"], new_pin_reset)
                            st.success("PIN Reset Successful! You can now login.")
                            del st.session_state["recovery_questions"]
                        else:
                            st.error("PIN must be 6 digits.")
                    else:
                        st.error("One or more answers are incorrect.")
