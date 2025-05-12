
from flask import Flask, render_template, request, jsonify
import csv
from collections import defaultdict
import requests
from skyfield.api import load, Topos
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import os
import math

app = Flask(__name__)

# Load planetary ephemeris data
planets = load('de421.bsp')
ts = load.timescale()

# Load location data from CSV
locations = defaultdict(lambda: defaultdict(set))
with open('data/locations.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        country = row['country']
        state = row['state']
        city = row['city']
        locations[country][state].add(city)
for country in locations:
    for state in locations[country]:
        locations[country][state] = list(locations[country][state])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_states')
def get_states():
    country = request.args.get('country')
    states = list(locations[country].keys())
    return jsonify(states)

@app.route('/get_cities')
def get_cities():
    country = request.args.get('country')
    state = request.args.get('state')
    cities = list(locations[country][state])
    return jsonify(cities)

@app.route('/get_chart', methods=['POST'])
def get_chart():
    data = request.get_json()
    birth_date = data['birth_date']
    birth_time = data['birth_time']
    country = data['country']
    state = data['state']
    city = data['city']
    lat = float(data['lat'])
    lon = float(data['lon'])

    # Determine timezone using timezonefinder
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    timezone = pytz.timezone(timezone_str)

    # Create datetime object for birth time
    dt_naive = datetime.strptime(f"{birth_date} {birth_time}", '%Y-%m-%d %H:%M')
    dt_local = timezone.localize(dt_naive)
    dt_utc = dt_local.astimezone(pytz.utc)

    # Convert to Skyfield time
    t = ts.from_datetime(dt_utc)
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)

    # Calculate planetary positions
    planets_dict = {
        "Sun": planets['sun'],
        "Moon": planets['moon'],
        "Mercury": planets['mercury'],
        "Venus": planets['venus'],
        "Mars": planets['mars'],
        "Jupiter": planets['jupiter barycenter'],
        "Saturn": planets['saturn barycenter']
    }

    eph = {}
    for name, body in planets_dict.items():
        astrometric = (planets['earth'] + observer).at(t).observe(body)
        ecl = astrometric.ecliptic_latlon()
        lon_deg = ecl[1].degrees
        eph[name] = lon_deg

    # Calculate Rahu and Ketu (mean lunar nodes, approx)
    moon_astrometric = (planets['earth'] + observer).at(t).observe(planets['moon'])
    moon_latlon = moon_astrometric.ecliptic_latlon()
    moon_long = moon_latlon[1].degrees

    # True node calculation would be more accurate; here we use approximation
    rahu = (moon_long + 180.0) % 360
    ketu = moon_long

    eph['Rahu'] = rahu
    eph['Ketu'] = ketu

    # Apply Lahiri Ayanamsa (approx. 23.85675 for year ~2025)
    ayanamsa = 23.85675
    eph_sidereal = {k: (v - ayanamsa) % 360 for k, v in eph.items()}

    # Compute Lagna (Ascendant)
    from skyfield.positionlib import ICRF
    from skyfield.almanac import ecliptic_position

    earth = planets['earth']
    astrometric = (earth + observer).at(t)
    gast = t.gast  # Greenwich Apparent Sidereal Time
    lagna = (gast * 15 + lon) % 360  # Simplified calculation

    eph_sidereal['Lagna'] = lagna

    return jsonify({
        "datetime_utc": dt_utc.isoformat(),
        "location": {"lat": lat, "lon": lon, "timezone": timezone_str},
        "ayanamsa": ayanamsa,
        "positions": eph_sidereal  # Sidereal positions
    })

if __name__ == "__main__":
    app.run(debug=True)
