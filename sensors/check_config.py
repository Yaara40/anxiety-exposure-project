import smbus
import time

bus = smbus.SMBus(1)
address = 0x57

print("=== Checking MAX30102 Configuration ===\\n")

# Read current settings BEFORE configuration
print("BEFORE configuration:")
mode_before = bus.read_byte_data(address, 0x09)
spo2_before = bus.read_byte_data(address, 0x0A)
led1_before = bus.read_byte_data(address, 0x0C)
led2_before = bus.read_byte_data(address, 0x0D)

print(f"Mode register (0x09): 0x{mode_before:02X}")
print(f"SpO2 config (0x0A): 0x{spo2_before:02X}")
print(f"LED1 current (0x0C): 0x{led1_before:02X}")
print(f"LED2 current (0x0D): 0x{led2_before:02X}")

print("\\n--- Writing configuration... ---\\n")

# Reset
bus.write_byte_data(address, 0x09, 0x40)
time.sleep(0.2)

# SpO2 mode
bus.write_byte_data(address, 0x09, 0x03)
time.sleep(0.1)

# SpO2 config
bus.write_byte_data(address, 0x0A, 0x27)
time.sleep(0.1)

# LED currents
bus.write_byte_data(address, 0x0C, 0xFF)
time.sleep(0.1)
bus.write_byte_data(address, 0x0D, 0xFF)
time.sleep(0.1)

print("AFTER configuration:")
mode_after = bus.read_byte_data(address, 0x09)
spo2_after = bus.read_byte_data(address, 0x0A)
led1_after = bus.read_byte_data(address, 0x0C)
led2_after = bus.read_byte_data(address, 0x0D)

print(f"Mode register (0x09): 0x{mode_after:02X}")
print(f"SpO2 config (0x0A): 0x{spo2_after:02X}")
print(f"LED1 current (0x0C): 0x{led1_after:02X}")
print(f"LED2 current (0x0D): 0x{led2_after:02X}")

print("\\n=== Analysis ===")
if mode_after == 0x03:
    print("Mode is correct (SpO2)")
else:
    print(f"Mode is wrong! Expected 0x03, got 0x{mode_after:02X}")

if led1_after == 0xFF and led2_after == 0xFF:
    print("LED currents are MAX")
else:
    print(f"LED currents wrong! LED1={led1_after:02X}, LED2={led2_after:02X}")

print("\nIf configuration is correct, sensor should work!")
