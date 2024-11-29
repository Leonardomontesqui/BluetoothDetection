import math
import asyncio
from bleak import BleakScanner
from datetime import datetime
from mac_vendor_lookup import MacLookup
import nest_asyncio
import os
from dotenv import load_dotenv

load_dotenv('.env.local')  # Load environment variables

# Constants
RSSI_AT_ONE = 50  # RSSI value at 1 meter
PATH_LOSS_EXP = 2  # Path loss exponent
DISTANCE_LIMIT = 20  # Maximum distance to consider a device in range (meters)
DISTANCE_TOLERANCE = 0.2  # Tolerance for grouping devices as one person
TIMEOUT_SECONDS = 10  # Time to scan for devices
SCAN_INTERVAL = 1  # Interval between scans
MIN_NON_ZERO_RSSI = 5  # Minimum non-zero RSSI values required for grouping

nest_asyncio.apply()

# HashMap to store RSSI history
rssi_history = {}

# Preload MAC vendor data
mac_lookup = MacLookup()
try:
    mac_lookup.load_vendors()
except Exception as e:
    print(f"Failed to preload vendor database: {e}")

def calculate_distance(rssi, rssi_at_1m=-RSSI_AT_ONE, path_loss_exponent=PATH_LOSS_EXP):
    """Calculates and rounds distance based on RSSI."""
    try:
        distance = 10 ** ((rssi_at_1m - rssi) / (10 * path_loss_exponent))
        return round(distance, 2)  # Round to 2 decimal places
    except Exception as e:
        print(f"Error calculating distance: {e}")
        return None

def update_rssi_history(address, rssi):
    """Updates the RSSI history for a given device and computes the average RSSI.
       If the list exceeds length 10, it pops the first element."""
    if address not in rssi_history:
        rssi_history[address] = []
    rssi_history[address].append(rssi)
    
    # Ensure the list doesn't exceed length 10 by popping the first element
    if len(rssi_history[address]) > 10:
        rssi_history[address].pop(0)
        
    return sum(rssi_history[address]) / len(rssi_history[address])

def mark_missing_devices(active_devices):
    """Marks devices that are no longer detected by adding a 0 to their RSSI history."""
    for address in rssi_history.keys():
        if address not in active_devices:
            rssi_history[address].append(0)

def group_devices_by_proximity(distances):
    """Groups devices by proximity within a specified tolerance."""
    distances.sort()
    groups = []
    current_group = []

    for distance in distances:
        if not current_group or abs(distance - current_group[-1]) <= DISTANCE_TOLERANCE:
            current_group.append(distance)
        else:
            groups.append(current_group)
            current_group = [distance]

    if current_group:
        groups.append(current_group)

    return groups  # Return groups of devices

def estimate_users_from_history():
    """Estimates users in the same vicinity using the RSSI history."""
    distances = []
    for address, rssi_values in rssi_history.items():
        non_zero_count = sum(1 for rssi in rssi_values if rssi != 0)
        if non_zero_count >= MIN_NON_ZERO_RSSI:  # Only consider devices with sufficient non-zero RSSI values
            avg_rssi = sum(rssi_values) / len(rssi_values)
            distance = calculate_distance(avg_rssi)
            if distance is not None and distance < DISTANCE_LIMIT:
                distances.append(distance)

    # Group devices by proximity
    groups = group_devices_by_proximity(distances)

    print("\nUsers grouped by proximity:")
    for i, group in enumerate(groups):
        print(f"Group {i + 1}: Devices at distances {group}")
    print(f"\nEstimated number of distinct users: {len(groups)}")

def print_filtered_rssi_history():
    """Prints devices with fewer than two '0's in their RSSI history."""
    print("\nFiltered RSSI History:")
    for address, rssi_values in rssi_history.items():
        if rssi_values.count(0) < 2:  # Check for fewer than two '0's
            print(f"Device: {address}, RSSI History: {rssi_values}")

async def count_devices():
    """Scans for Bluetooth devices, calculates distances, and estimates people count."""
    try:
        devices = await BleakScanner.discover(timeout=TIMEOUT_SECONDS)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Total devices found: {len(devices)}")

        distances = []
        active_devices = []

        for device in devices:
            active_devices.append(device.address)
            avg_rssi = update_rssi_history(device.address, device.rssi)
            distance = calculate_distance(avg_rssi)
            if distance is not None and distance < DISTANCE_LIMIT:
                distances.append(distance)

        # Mark devices not detected in this scan
        mark_missing_devices(active_devices)

        print("\nDevices within range:")
        for i, distance in enumerate(distances):
            print(f"Device {i + 1}: Distance = {distance:.2f} meters")

        # Count people based on device grouping
        groups = group_devices_by_proximity(distances)
        print(f"\nEstimated number of people: {len(groups)}")

        # Print filtered RSSI history
        print_filtered_rssi_history()

        # Estimate users from RSSI history
        estimate_users_from_history()

    except Exception as e:
        print(f"Error: {e}")

async def continuous_count():
    """Continuously scans for Bluetooth devices at regular intervals."""
    try:
        while True:
            await count_devices()
            await asyncio.sleep(SCAN_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped scanning")

if __name__ == "__main__":
    print("Starting Bluetooth device scanner...")
    print("Press Ctrl+C to stop")
    asyncio.run(continuous_count())
