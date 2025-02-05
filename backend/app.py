from flask import Flask, request, jsonify
import mysql.connector
import google.generativeai as genai
from flask_cors import CORS
import json
import decimal
import re

app = Flask(__name__)
CORS(app)

# Set up API key for Gemini (or another LLM model)
genai.configure(api_key="AIzaSyDAjN9WiI--KNg2bQ1CuGMSVKnAFWWOQSc")
model = genai.GenerativeModel("gemini-1.5-flash")

# MySQL Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="prakhars",
        database="chatbot"
    )

def save_chat_history(user_message, bot_response):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_message, bot_response) VALUES (%s, %s)",
        (user_message, bot_response)
    )
    conn.commit()
    cursor.close()
    conn.close()

# Function to fetch product data based on query    
def fetch_products(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if "price" in query.lower():
        # Extracting specific product or brand for price
        if "Macbook Pro" in query:
            cursor.execute("SELECT name, price FROM products WHERE name LIKE %s", ("%Macbook Pro%",))
        elif "Apple" in query:
            cursor.execute("SELECT name, price FROM products WHERE brand LIKE %s", ("%Apple%",))
        else:
            cursor.execute("SELECT name, price FROM products")  # Default: Get product names and prices

    elif "brand" in query.lower():
        if "Macbook Pro" in query:
            cursor.execute("SELECT name, price FROM products WHERE name LIKE %s", ("%Macbook Pro%",))
        elif "Apple" in query:
            cursor.execute("SELECT name, price FROM products WHERE brand LIKE %s", ("%Apple%",))
        else:
            cursor.execute("SELECT DISTINCT brand FROM products")
    elif "laptop" in query.lower():
        cursor.execute("SELECT name, price FROM products WHERE category LIKE %s", ("%laptop%",))
    elif "smartphone" in query.lower():
        cursor.execute("SELECT name, price FROM products WHERE category LIKE %s", ("%smartphone%",))
    
    else:
        cursor.execute("SELECT * FROM products")  # Default: Get all products (used if no other match)

    products = cursor.fetchall()

    # Convert Decimal to float for JSON serializability
    for product in products:
        for key, value in product.items():
            if isinstance(value, decimal.Decimal):
                product[key] = float(value)

    cursor.close()
    conn.close()
    return products

# Function to fetch supplier information based on query
def fetch_suppliers(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Query handling for fetching supplier info
    if "contact" in query.lower():
        cursor.execute("SELECT name, contact_info, product_categories_offered FROM suppliers")
    elif "laptop" in query.lower():
        cursor.execute("SELECT name, contact_info, product_categories_offered FROM suppliers WHERE product_categories_offered LIKE %s", ("%laptops%",))
    elif "smartphone" in query.lower():
        cursor.execute("SELECT name, contact_info, product_categories_offered FROM suppliers WHERE product_categories_offered LIKE %s", ("%smartphones%",))
    elif "Apple" in query.lower():
        cursor.execute("SELECT name, contact_info, product_categories_offered FROM suppliers WHERE product_categories_offered LIKE %s", ("%Apple%",))
    elif "supplier" in query.lower():
        cursor.execute("SELECT name, contact_info, product_categories_offered FROM suppliers")  # Get all suppliers
    else:
        cursor.execute("SELECT name, contact_info, product_categories_offered FROM suppliers")  # Default: Get all suppliers

    suppliers = cursor.fetchall()

    # Convert Decimal to float for JSON serializability
    for supplier in suppliers:
        for key, value in supplier.items():
            if isinstance(value, decimal.Decimal):
                supplier[key] = float(value)

    cursor.close()
    conn.close()
    return suppliers

# Function to generate enhanced response using the Gemini model
def generate_gemini_response(data, query_type):
    try:
        prompt = f"Based on the following data, provide a detailed summary. {query_type} information: {json.dumps(data)}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # Fetch products or suppliers based on user query
    if "price" in user_message.lower() or "brand" in user_message.lower() or "product" in user_message.lower():
        # Fetch product-related data (price or brand info)
        products = fetch_products(user_message)
        bot_response = generate_gemini_response(products, "Product Price/Brand")
    elif "contact_info" in user_message.lower() or "supplier" in user_message.lower():
        # Fetch supplier data (including contact information and categories)
        suppliers = fetch_suppliers(user_message)
        bot_response = generate_gemini_response(suppliers, "Supplier Contact Info")
    else:
        bot_response = "Sorry, I couldn't understand the query."
    save_chat_history(user_message, bot_response)
    return jsonify({'message': bot_response})

@app.route('/history', methods=['GET'])
def history():
    # Fetch recent chat history from the database (optional)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_message, bot_response FROM chat_history ORDER BY timestamp DESC LIMIT 3")
    chat_history = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(chat_history)

if __name__ == '__main__':
    app.run(debug=True)
