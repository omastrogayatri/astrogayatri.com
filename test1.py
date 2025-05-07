from skyfield.api import load

planets = load('de440s.bsp')
print("Loaded planets:", planets.names())