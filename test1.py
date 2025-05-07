from skyfield.api import load

planets = load('de440s.bsp')  # or your full path

print("Available targets in the kernel:")
for target in planets.names():
    print(target)