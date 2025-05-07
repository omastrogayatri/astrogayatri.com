from flask import Flask, render_template, request, jsonify
import csv
from collections import defaultdict
import requests
from skyfield.api import load, Topos
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

app = Flask(__name__)

if __name__ == "__main__":
   app.run(debug=True)

# Load CSV data into nested dict structure
locations = defaultdict(lambda: defaultdict(set))

with open('data/locations.csv', newline='', encoding='utf-8') as csvfile:
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

def get_zodiac_sign(ecl_lon_deg):
    ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
    return ZODIAC_SIGNS[int(ecl_lon_deg // 30)]

@app.route('/submit', methods=['POST'])
def submit():
    
    name = request.form['name']
    dob = request.form['dob']
    tob = request.form['tob']
    country = request.form['country']
    state = request.form['state']
    city = request.form['city']

    # Compose input for LLM

    #get latitude, longitude

    url = f"https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{city}, {state}, {country}",
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': 'kundali-app'}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if not data:
        raise Exception("Location not found.")
    lat = float(data[0]['lat'])
    lon = float(data[0]['lon'])
   
  # timezone finder
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    dt_naive = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    tz = pytz.timezone(tz_name)
    dt_local = tz.localize(dt_naive)
    dt_utc = dt_local.astimezone(pytz.utc)


    planets = load('de421.bsp')
    ts = load.timescale()
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute)

    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
    earth = planets['earth']

    print(f"\nKundali for {name} in {city}, {state}, {country}")
    print(f"Local Time: {dt_local} | UTC: {dt_utc}")
    print("-" * 60)
    print(f"{'Planet':<10} {'Longitude (°)':<15} {'Zodiac Sign':<10}")
    print("-" * 60)
    
    
    # Map of planet names to NAIF IDs (matching de421.bsp)
    planet_ids = {
    'Sun': 10,
    'Moon': 301,
    'Mercury': 199,
    'Venus': 299,
    'Mars': 499,
    'Jupiter': 599,
    'Saturn': 699
    }

    for planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
     try:
        body = planets[planet_ids[name]]
        astrometric = (earth + observer).at(t).observe(body).apparent()
        ecliptic = astrometric.ecliptic_latlon()
        lon_deg = ecliptic[1].degrees
        sign = get_zodiac_sign(lon_deg)
        print(f"{name:<10} {lon_deg:<15.2f} {sign:<10}")
     except KeyError:
        print(f"{name:<10} {'N/A':<15} {'Not in kernel':<10}")

     #birth_details = f"Name: {name}, DOB: {dob}, Time: {tob}, Location: {location}"

    # Call Hugging Face Mistral model via API (assume hosted version)
   # response = requests.post(
    #    "https://api-inference.huggingface.co/models/your-username/mistral-kundali",
     #   headers={"Authorization": f"Bearer YOUR_HUGGINGFACE_API_TOKEN"},
      #  json={"inputs": f"Generate a detailed Vedic kundali interpretation for: {birth_details}"}
    #) 

    #result = response.json()[0]["generated_text"]
    #return f"<h2>Your Kundali:</h2><pre>{result}</pre>"
