from flask import Flask, request, render_template
import requests

app = Flask(_name_)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generate', methods=['POST'])
def generate_kundali():
    name = request.form['name']
    dob = request.form['dob']
    tob = request.form['tob']
    location = request.form['location']

    # Compose input for LLM
    birth_details = f"Name: {name}, DOB: {dob}, Time: {tob}, Location: {location}"

    # Call Hugging Face Mistral model via API (assume hosted version)
    response = requests.post(
        "https://api-inference.huggingface.co/models/your-username/mistral-kundali",
        headers={"Authorization": f"Bearer YOUR_HUGGINGFACE_API_TOKEN"},
        json={"inputs": f"Generate a detailed Vedic kundali interpretation for: {birth_details}"}
    )

    result = response.json()[0]["generated_text"]
    return f"<h2>Your Kundali:</h2><pre>{result}</pre>"