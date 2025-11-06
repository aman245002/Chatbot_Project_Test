import streamlit as st
import pandas as pd
import psycopg2
from groq import Groq
import os

# --- 1. SET UP PAGE AND API KEYS ---
st.set_page_config(page_title="Personal Care Bot", layout="centered")
st.title("🛍️ Myntra Personal Care Bot")
st.write("This bot uses a CSV file scraped from Myntra to answer product questions.")

# --- 2. LOAD SCRAPED DATA ---
@st.cache_data
def load_product_data():
    """Loads the scraped product data from the CSV file."""
    try:
        df = pd.read_csv("myntra_products.csv").head(20)
        # Convert the dataframe to a simple string format for the LLM
        return df.to_string(index=False)
    except FileNotFoundError:
        st.error("Error: myntra_products.csv file not found.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        st.stop()

product_data_string = load_product_data()

# --- 3. DATABASE SETUP ---
# We will use Streamlit secrets to store the DB URL and API key
# This is required for deployment and works locally too.
try:
    db_url = st.secrets["DB_URL"]
    groq_api_key = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("ERROR: Please set GROQ_API_KEY and DB_URL in your Streamlit secrets.")
    st.info("Create a file .streamlit/secrets.toml with your keys.")
    st.stop()

@st.cache_resource
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def log_message(conn, role, content):
    """Logs a single chat message to the database."""
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_logs (role, content) VALUES (%s, %s)",
                    (role, content)
                )
                conn.commit()
        except Exception as e:
            # Don't stop the app, just log the error to the console
            print(f"Failed to log message: {e}") 

# Initialize connection
db_conn = get_db_connection()

# --- 4. CHATBOT LOGIC ---

# System Prompt: This tells the AI how to behave.
SYSTEM_PROMPT = f"""
You are a helpful assistant for the Myntra personal care website.
Your role is to answer questions about lipstick products based *only* on the data provided.

You MUST use the following product data to answer questions.
Do not make up products or prices. If a product is not in the list, say so.
When a user asks for a specific product, provide its name, price, and product_url.

--- PRODUCT DATA ---
{product_data_string}
--- END PRODUCT DATA ---

If the user asks for a "link" or "URL", you should provide the 'product_url'.
If the user asks for the "category" or "path", you should provide the 'breadcrumbs'.

If the user asks a general question (like "how to apply lipstick?"),
you can answer it helpfully.
"""

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. HANDLE USER INPUT ---
if prompt := st.chat_input("Ask me about our lipstick products..."):
    
    # --- THIS IS THE KEYWORD REDIRECTION ---
    user_input_lower = prompt.lower()
    keywords = ["offer", "return", "discount", "refund", "complaint", "coupon"]

    if any(keyword in user_input_lower for keyword in keywords):
        # 1. Create the redirection response
        response = (
            "I see you're asking about offers or returns. "
            "For that, you'll need to speak with a human representative. \n\n"
            "**Please call our support team at: (555) 123-4567**"
        )
        
        # 2. Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 3. Add bot response to history and display it
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
            
        # 4. Log BOTH messages to the database
        log_message(db_conn, "user", prompt)
        log_message(db_conn, "assistant", response)

    else:
        # --- THIS IS THE NORMAL LLM CHAT ---
        
        # 1. Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # 2. Log user message to database
        log_message(db_conn, "user", prompt)

        # 3. Prepare message list for Groq API
        # We add the system prompt + all chat history
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages

        # 4. Call the Groq API
        try:
            chat_completion = client.chat.completions.create(
                messages=api_messages,
                model="llama-3.1-8b-instant", # This is a current, active model # The latest fast model from Google # A fast and capable model from Google # Fast and capable model
                temperature=0.7,
            )
            response = chat_completion.choices[0].message.content
        
        except Exception as e:
            response = f"Sorry, I had trouble connecting to the AI model. Error: {e}"

        # 5. Add bot response to history and display it
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
            
        # 6. Log bot response to database
        log_message(db_conn, "assistant", response)

# Note: The database connection will close automatically when the script ends/re-runs