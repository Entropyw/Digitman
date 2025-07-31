import matplotlib.pyplot as plt
import numpy as np

# Precompute factorials
lx = [1] * 250
for i in range(1, 250):
    lx[i] = lx[i-1] * i

def C(n, k):
    return lx[n] // lx[k] // lx[n - k] if k <= n else 0

# Initialize results arrays
results1 = [(250, 0)] * 250
results2 = [(0, 0)] * 250

p0 = 0.1
p1 = 0.05
p2 = 0.1

# Calculate results
for i in range(1, 250):
    sump = 0.0
    for j in range(0, min(i, 30)):
        sump += C(i, j) * (p0 ** j) * ((1 - p0) ** (i - j))
        if sump >= 1 - p1:
            results1[j] = (i, 1 - sump)
        if sump <= p2 and results2[j][0] == 0:
            results2[j] = (i, sump)

# Extract x and y values for plotting
x1 = [0, 0]
for i in range(30):
    if results1[i][0] < 250: x1.append(results1[i][0])
y1 = list(range(len(x1)))
x2 = [results2[j][0] for j in range(30) if results2[j][0] > 0]
y2 = list(range(len(x2)))

# Truncate to the shortest common length
min_length = min(len(x1), len(x2))
x1 = x1[:min_length]
y1 = y1[:min_length]
x2 = x2[:min_length]
y2 = y2[:min_length]

# Create the plot
plt.figure(figsize=(10, 8))

# Plot lines
plt.plot(x1, y1, 'b-', label='p > 0.1,Confidence = 90%')
plt.plot(x2, y2, 'r-', label='p < 0.1,Confidence = 90%')

# Shade regions
plt.fill_betweenx(y1, x1, 250, color='red', alpha=0.2, label='Rejection region')
plt.fill_betweenx(y2, 0, x2, color='green', alpha=0.2, label='Acceptance region')
plt.fill_betweenx(y1, x2, x1, color='yellow', alpha=0.1, label='Pending region')

# Mark specific points with coordinates
points_to_mark = [5, 10, 15, 20, 25]
for idx in points_to_mark:
    if idx < len(x1):
        plt.plot(x1[idx], y1[idx], 'bo')
        plt.text(x1[idx] + 5, y1[idx], f'({x1[idx]}, {y1[idx]})', fontsize=8)
    if idx < len(x2):
        plt.plot(x2[idx], y2[idx], 'ro')
        plt.text(x2[idx] + 5, y2[idx], f'({x2[idx]}, {y2[idx]})', fontsize=8)

# Set axis limits and labels
plt.xlim(0, 250)
plt.ylim(0, min_length)
plt.xlabel('Sample Size (n)')
plt.ylabel('Number of defective products (k)')
plt.title('Test results')
plt.legend()
plt.grid(True)

# Show plot
plt.show()