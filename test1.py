from skyfield.api import Loader
load = Loader('~/skyfield-data')
planets = load('C:\\Users\\a33\\skyfield-data\\de440.bsp')
print("Loaded planets:", planets.names())
print(planets.filename)