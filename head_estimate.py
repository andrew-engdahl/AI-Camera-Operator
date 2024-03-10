torsoPoints = {'x': {11: 0.69, 12: 0.27, 23: 0.6, 24: 0.34}, 'y': {11: 0.68, 12: 0.68, 23: 1.37, 24: 1.37}}

print(max(zip(torsoPoints.values(), torsoPoints.keys()))[1])