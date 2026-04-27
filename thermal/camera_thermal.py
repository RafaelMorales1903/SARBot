import time

import numpy as np

import matplotlib.pyplot as plt

from scipy.interpolate import griddata

from smbus2 import SMBus



# Direccion I2C del sensor AMG8833

AMG88xx_ADDR = 0x69

# Registros del sensor

AMG88xx_PIXEL_OFFSET = 0x80



bus = SMBus(1)



def read_temp():

# Lee los 64 pixeles (2 bytes cada uno)

status = bus.read_i2c_block_data(AMG88xx_ADDR, AMG88xx_PIXEL_OFFSET, 32)

status2 = bus.read_i2c_block_data(AMG88xx_ADDR, AMG88xx_PIXEL_OFFSET + 32, 32)

status3 = bus.read_i2c_block_data(AMG88xx_ADDR, AMG88xx_PIXEL_OFFSET + 64, 32)

status4 = bus.read_i2c_block_data(AMG88xx_ADDR, AMG88xx_PIXEL_OFFSET + 96, 32)


all_data = status + status2 + status3 + status4

pixels = []

for i in range(0, 128, 2):

# Convertir bytes a temperatura Celsius

val = (all_data[i+1] << 8) | all_data[i]

if val & 0x800:

val -= 0x1000

pixels.append(val * 0.25)

return np.array(pixels).reshape(8, 8)



# Configurar grafica

plt.ion()

fig, ax = plt.subplots(figsize=(6, 6))

im = ax.imshow(np.zeros((32, 32)), cmap='inferno', interpolation='gaussian')

plt.colorbar(im)



print("Iniciando lectura térmica...")



try:

while True:

pixels = read_temp()


# Suavizado de imagen

points = np.mgrid[0:8, 0:8].reshape(2, -1).T

values = pixels.flatten()

grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]

bicubic = griddata(points, values, (grid_x, grid_y), method='cubic')


im.set_data(bicubic)

im.set_clim(vmin=np.min(bicubic), vmax=np.max(bicubic))

plt.pause(0.01)

except Exception as e:

print(f"Error: {e}")

finally:

bus.close()