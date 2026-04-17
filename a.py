import matplotlib.pyplot as plt
import re

ticks = []
brightness = []
light_level = []
sky_r = []
sky_g = []
sky_b = []

with open("test.txt") as f:
    for line in f:
        try:
            # Example line: Tick: 0, Brightness: 1.000, Light Level: 15, Sky RGB: (135, 205, 234)
            t_match = re.search(r"Tick:\s*(\d+)", line)
            b_match = re.search(r"Brightness:\s*([\d.]+)", line)
            l_match = re.search(r"Light Level:\s*(\d+)", line)
            rgb_match = re.search(r"Sky RGB:\s*\((\d+),\s*(\d+),\s*(\d+)\)", line)

            if t_match and b_match and l_match and rgb_match:
                ticks.append(int(t_match.group(1)))
                brightness.append(float(b_match.group(1)))
                light_level.append(int(l_match.group(1)))
                r, g, b_col = map(int, rgb_match.groups())
                sky_r.append(r)
                sky_g.append(g)
                sky_b.append(b_col)
            else:
                print(f"Skipping malformed line: {line.strip()}")
        except Exception as e:
            print(f"Error parsing line: {line.strip()} — {e}")

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(ticks, brightness, label="Brightness", color="gold")
plt.plot(ticks, light_level, label="Light Level", color="gray")
plt.plot(ticks, sky_r, label="Sky R", color="red", linestyle="--")
plt.plot(ticks, sky_g, label="Sky G", color="green", linestyle="--")
plt.plot(ticks, sky_b, label="Sky B", color="blue", linestyle="--")
plt.xlabel("Tick")
plt.ylabel("Value")
plt.title("Sky Light vs Block Light Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("sky_light_plot.png")
print("Plot saved as sky_light_plot.png")

