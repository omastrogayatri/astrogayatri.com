from skyfield.api import load
planets = load('de421.bsp')
print("Loaded planets:", planets.names())
print(planets.filename)