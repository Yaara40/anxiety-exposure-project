import smbus2
import time

bus = smbus2.SMBus(1)
MAX30100_ADDRESS = 0x57

def write_register(reg, value):
    bus.write_byte_data(MAX30100_ADDRESS, reg, value)
    time.sleep(0.01)

def read_register(reg):
    return bus.read_byte_data(MAX30100_ADDRESS, reg)

# Reset
write_register(0x09, 0x40)
time.sleep(0.2)

# Wake up
write_register(0x09, 0x02)  # HR mode (?? SpO2)
time.sleep(0.1)

# Sample rate + LED pulse width
write_register(0x0A, 0x17)  # 100 samples/sec, 1600us pulse
# LED currents - max
write_register(0x0B, 0xFF)

print("Part ID:", hex(read_register(0xFF)))
print("Mode:", hex(read_register(0x09)))
print("\nReading - put finger on sensor")

for i in range(100):
    wr = read_register(0x04)
    rd = read_register(0x06)
    print(f"WR: {wr} RD: {rd}")
    if wr != rd:
        data = bus.read_i2c_block_data(MAX30100_ADDRESS, 0x05, 4)
        ir = (data[0] << 8) | data[1]
        print(f"IR: {ir}")
    time.sleep(0.1)
