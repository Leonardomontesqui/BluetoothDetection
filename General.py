import asyncio
from bleak import BleakScanner
import numpy as np

class PeopleDetector:
    def __init__(self, max_distance=3.0, distance_threshold=1.0, scan_duration=10):
        """
        Initialize the detector with user-defined settings.
        :param max_distance: Maximum distance (in meters) to detect devices
        :param distance_threshold: Distance (in meters) to group devices (default: 1.0 m)
        :param scan_duration: Duration of the scan in seconds (default: 10 s)
        """
        self.max_distance = max_distance  # Maximum distance (in meters) to detect devices
        self.distance_threshold = distance_threshold  # Distance (in meters) for grouping
        self.scan_duration = scan_duration  # Scan duration in seconds
        self.rssi_threshold = self._calculate_rssi_threshold(self.max_distance)  # Calculate RSSI threshold based on max_distance

    def _calculate_rssi_threshold(self, max_distance):
        """
        Calculate the RSSI threshold for a given maximum distance.
        :param max_distance: Maximum detection distance in meters
        :return: RSSI threshold in dBm
        """
        tx_power = -59  # Assumed transmission power in dBm (adjust if necessary)
        path_loss_exponent = 2.5  # Adjusted for typical indoor environments

        # RSSI calculation based on distance
        rssi = tx_power - 10 * path_loss_exponent * np.log10(max_distance)

        return rssi

    async def scan_and_detect(self):
        print(f"🔍 Starting Bluetooth scan for {self.scan_duration} seconds...")

        # Create scanner
        scanner = BleakScanner()
        await scanner.start()

        # Scan for the specified duration
        await asyncio.sleep(self.scan_duration)

        # Get discovered devices
        devices = await scanner.get_discovered_devices()
        await scanner.stop()

        # Filter and calculate distances
        device_distances = []
        for device in devices:
            if device.rssi and device.rssi > self.rssi_threshold:  # Filter weak signals
                # Add multiple readings to average out noise
                distances = [self._calculate_distance(device.rssi) for _ in range(5)]  # 5 readings
                averaged_distance = np.mean([d for d in distances if d is not None])
                if averaged_distance is not None:
                    device_distances.append(averaged_distance)
                    print(f"Device: {device.address}, RSSI: {device.rssi}, Averaged Distance: {averaged_distance:.2f} m")

        # Group devices into "people" based on proximity
        people_count = self._group_by_distance(device_distances)
        print(f"\n👥 Total Number of People Detected: {people_count}")
        return people_count

    def _calculate_distance(self, rssi):
        """
        Calculate approximate distance from RSSI using a simplified path loss model.
        :param rssi: Received Signal Strength Indicator (in dBm)
        :return: Distance in meters
        """
        tx_power = -59  # Assumed transmission power in dBm (adjust if necessary)
        path_loss_exponent = 2.5  # Adjusted for typical indoor environments

        # Distance calculation based on RSSI
        distance = 10 ** ((tx_power - rssi) / (10 * path_loss_exponent))

        # Cap unrealistic distances
        if distance > self.max_distance:
            return None
        return distance

    def _group_by_distance(self, distances):
        """
        Groups devices into 'people' based on proximity.
        Assumes devices closer than `distance_threshold` belong to the same person.
        :param distances: List of device distances in meters
        :return: Number of unique "people" detected
        """
        distances.sort()  # Sort distances for easier grouping
        people_count = 0
        i = 0

        while i < len(distances):
            # Start a new group for this device
            people_count += 1
            current_distance = distances[i]

            # Skip all devices within the distance threshold plus a buffer zone
            while i < len(distances) and distances[i] - current_distance <= (self.distance_threshold + 0.2):  # Adjust buffer zone
                i += 1

        return people_count

    def run_scan(self):
        """
        Run the asynchronous scan and return the number of detected people.
        """
        return asyncio.run(self.scan_and_detect())

def main():
    # User-defined settings (adjustable)
    max_distance = 15.0  # Maximum detection distance (in meters)
    distance_threshold = 0.5  # Distance (in meters) to group devices as one person
    scan_duration = 10  # Scan duration in seconds

    detector = PeopleDetector(
        max_distance=max_distance,
        distance_threshold=distance_threshold,
        scan_duration=scan_duration
    )
    people_count = detector.run_scan()
    print(f"\n🏁 Scan Complete. Number of People Detected: {people_count}")

if __name__ == "__main__":
    main()
