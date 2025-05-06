from flask import Flask, render_template, request, jsonify
import csv
from collections import defaultdict

app = Flask(__name__)

# Load CSV data into nested dict structure
locations = defaultdict(lambda: defaultdict(set))

with open('locations.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        country = row['country']
        state = row['state']
        city = row['city']
        locations[country][state].add(city)

# Convert sets to lists for JSON serialization
for country in locations:
    for state in locations[country]:
        locations[country][state] = list(locations[country][state])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_states')
def get_states():
    country = request.args.get('country')
    states = list(locations.get(country, {}).keys())
    return jsonify(states)

@app.route('/get_cities')
def get_cities():
    state = request.args.get('state')
    for country_data in locations.values():
        if state in country_data:
            return jsonify(country_data[state])
    return jsonify([])

@app.route('/submit', methods=['POST'])
def submit():
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
