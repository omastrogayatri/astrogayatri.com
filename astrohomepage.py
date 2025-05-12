from flask import Flask, render_template, request, jsonify
import csv
from collections import defaultdict
import requests
from skyfield.api import load, Topos
from skyfield.positionlib import ICRF
#from skyfield.almanac import ecliptic_position
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import os
import urllib.request

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
    BSP_FILE1 = 'de421.bsp'
    #BSP_URL1 = 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp'
    BSP_FILE2 = 'sat361.bsp'
    #BSP_URL2 = 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/a_old_versions/sat361.bsp'
    BSP_FILE3 = 'jup329.bsp'
    BSP_URL3 = 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/a_old_versions/jup329.bsp'

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
   
    # Determine timezone using timezonefinder
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    tz = pytz.timezone(tz_name)
    # Create datetime object for birth time
    dt_naive = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    dt_local = tz.localize(dt_naive)
    dt_utc = dt_local.astimezone(pytz.utc)


# Download if file is missing
    #if not os.path.exists(BSP_FILE1):
    #print("Downloading de421.bsp")
    #urllib.request.urlretrieve(BSP_URL1, BSP_FILE1)
    #print("Download complete.")

    #if not os.path.exists(BSP_FILE2):
    #print("Downloading sat454.bsp")
    #urllib.request.urlretrieve(BSP_URL2, BSP_FILE2)
    #print("Download complete.")

    if not os.path.exists(BSP_FILE3):
      print("Downloading jup329.bsp")
      urllib.request.urlretrieve(BSP_URL3, BSP_FILE3)
      print("Download complete.")

    planets = load(BSP_FILE1)
    satplanet = load('sat361.bsp')
    jupplanet = load('jup329.bsp')

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
    ayanamsa = 23.85675
    eph = {}
    for planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn','RahuKetu']:
     try:
        if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']:
            body = planets[planet_ids[planet_name]]
            astrometric = (earth + observer).at(t).observe(body).apparent()
            ecliptic = astrometric.ecliptic_latlon()
            lon_deg = ecliptic[1].degrees
            sidereal_lon = (lon_deg - ayanamsa) % 360
            sign = get_zodiac_sign(sidereal_lon)
            eph[planet_name] = { "Longitude": lon_deg, "Sign": sign }
            print(f"{planet_name:<10} {lon_deg:<15.2f} {sign:<10}")
        if planet_name in ['Jupiter']:
            body = jupplanet[planet_ids[planet_name]]
            astrometric = (earth + observer).at(t).observe(body).apparent()
            ecliptic = astrometric.ecliptic_latlon()
            lon_deg = ecliptic[1].degrees
            sidereal_lon = (lon_deg - ayanamsa) % 360
            sign = get_zodiac_sign(sidereal_lon)
            eph[planet_name] = { "Longitude": lon_deg, "Sign": sign }
            print(f"{planet_name:<10} {lon_deg:<15.2f} {sign:<10}")
        if planet_name in ['Saturn']:
            body = satplanet[planet_ids[planet_name]]
            astrometric = (earth + observer).at(t).observe(body).apparent()
            ecliptic = astrometric.ecliptic_latlon()
            lon_deg = ecliptic[1].degrees
            sidereal_lon = (lon_deg - ayanamsa) % 360
            sign = get_zodiac_sign(sidereal_lon)
            eph[planet_name] = { "Longitude": lon_deg, "Sign": sign }
            print(f"{planet_name:<10} {lon_deg:<15.2f} {sign:<10}")    
        if planet_name in ['RahuKetu']:
            body = planets[planet_ids['Moon']]
            astrometric = (earth + observer).at(t).observe(body)
            ecliptic = astrometric.ecliptic_latlon()
            lon_deg = ecliptic[1].degrees
            rahu = (lon_deg + 180.0) % 360
            ketu = lon_deg
            rahusiderl_lon = (rahu - ayanamsa) % 360
            ketusiderl_lon = (ketu - ayanamsa) % 360
            rahusign = get_zodiac_sign(rahusiderl_lon)
            ketusign = get_zodiac_sign(ketusiderl_lon)

            eph['Rahu'] = { "Longitude": rahusiderl_lon, "Sign": rahusign }
            print(f"Rahu: {rahusiderl_lon:<15.2f} {rahusign:<10}")      

            eph['Ketu'] = { "Longitude": ketusiderl_lon, "Sign": ketusign }
            print(f"Ketu: {ketusiderl_lon:<15.2f} {ketusign:<10}")  
     except KeyError:
      print(f"{planet_name:<10} {'N/A':<15} {'Not in kernel':<10}")

    # Compute Lagna (Ascendant)

    gast = t.gast  # Greenwich Apparent Sidereal Time
    lagna = (gast * 15 + lon) % 360  # Simplified calculation
    eph['Lagna'] = { "Longitude": lagna }


# Loop to print the key and values
    for key, value in eph.items():
     print(f"Key: {key}")
     for sub_key, sub_value in value.items():
      print(f"  {sub_key}: {sub_value}")

    #Together AI call
    TOGETHER_API_KEY = "tgp_v1_xekeicYc2vvaUxUnpuWODX3q1LLMf-x4MCO5HYY6mmc"
    TOGETHER_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # You can change model
 
    

#def generate_kundali_from_api(name, dob, time, location, eph_data):
    prompt = f"""
    Generate a detailed Janm Kundali in traditional Vedic astrology style for:
    Name: {name}
    Date of Birth: {dob}
    Time of Birth: {tob}
    Place of Birth: {city}, {state}, {country}
    Planetary data: {eph}

    Please include general personality, strengths, career, marriage, health, challenges, and planetary effects.
    """

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": TOGETHER_MODEL,
        "prompt": prompt,
        "max_tokens": 600,
        "temperature": 0.7
    }

    response = requests.post("https://api.together.xyz/v1/completions", headers=headers, json=data)
    if response.status_code == 200:
        kundali_text = response.json()['choices'][0]['text'].strip()
        return render_template('kundali.html', kundali=kundali_text)
    else:
        return f"Error: {response.text}"


     #birth_details = f"Name: {name}, DOB: {dob}, Time: {tob}, Location: {location}"

    # Call Hugging Face Mistral model via API (assume hosted version)
   # response = requests.post(
    #    "https://api-inference.huggingface.co/models/your-username/mistral-kundali",
     #   headers={"Authorization": f"Bearer YOUR_HUGGINGFACE_API_TOKEN"},
      #  json={"inputs": f"Generate a detailed Vedic kundali interpretation for: {birth_details}"}
    #) 

    #result = response.json()[0]["generated_text"]
    #return f"<h2>Your Kundali:</h2><pre>{result}</pre>"
