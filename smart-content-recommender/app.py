from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import google.generativeai as genai
import os

app = Flask(__name__)

# === CONFIGURE YOUR API KEY & MONGODB URI ===
genai.configure(api_key="AIzaSyCN0m7WYw9yjLxhTDfFGT-vDqrpTD0x6ko")
mongo_uri = "mongodb+srv://adyabhat0201:b8j56SWILS8kt6fg@cluster0.nml8zpn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB Atlas
client = MongoClient(mongo_uri)
db = client["content_recommendation"]
collection = db["user_queries"]

# === Gemini AI Function ===
def generate_content_and_links(question):
    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
        response = model.generate_content(
            contents=[{"role": "user", "parts": [question]}]
        )
        return response.text
    except Exception as e:
        print("Gemini error:", e)
        return "Sorry, I couldn't generate a response right now."

# === Routes ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    username = data.get('username')
    question = data.get('question')

    if not username or not question:
        return jsonify({'error': 'Missing fields'}), 400

    ai_response = generate_content_and_links(question)

    # Save to MongoDB
    collection.insert_one({
        'username': username,
        'question': question,
        'response': ai_response
    })

    return jsonify({'response': ai_response})

@app.route('/history/<username>')
def user_history(username):
    # Fetch past queries/responses from MongoDB
    history = list(collection.find({'username': username}))
    return render_template('history.html', username=username, history=history)


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5002, debug=True)