#!/usr/bin/env python3
"""
GPS Spoofing script - "Slow Drift" Experiment


This script implements GPS spoofing for a stationary ArduPilot fixed wing SITL by:
1. Configuring GPS parameters via MAVLink (GPS2_TYPE=14, GPS_AUTO_SWITCH=0, GPS_PRIMARY=1)
2. Synchronizing with GPS1's current position, once.
3. Injecting GPS_INPUT messages for GPS instance 1 (GPS2)
4. Gradually drifting the spoofed GPS position to test EKF resilience

Usage:

Basic usage with default settings
python3 spoof_gps_drift.py

Drift east at 1 m/s for 60 seconds
python3 spoof_gps_drift.py --drift-rate 1.0 --drift-direction 90 --duration 60

Skip parameter configuration (manual setup)
python3 spoof_gps_drift.py --skip-params
        
"""

import time
import argparse
import math
import sys
from pymavlink import mavutil
from datetime import datetime, timezone

# Constants
GPS_FIX_TYPE_3D = 3
GPS_INSTANCE_1 = 1  # Second GPS instance
EARTH_RADIUS_M = 6371000.0  # meters

class GPSSpoofing:
    def __init__(self, connection_string, skip_params=False):
        """Initialize GPS spoofing connection."""
        print(f"[*] Connecting to ArduPilot at {connection_string}...")
        self.master = mavutil.mavlink_connection(connection_string)
        
        # Wait for heartbeat
        print("[*] Waiting for heartbeat...")
        self.master.wait_heartbeat()
        print(f"[+] Heartbeat received! System ID: {self.master.target_system}, Component ID: {self.master.target_component}")
        
        # State variables
        self.gps1_lat = None # static
        self.gps1_lon = None # static
        self.gps1_alt = None # static
        self.synchronized = False
        self.drift_offset_north = 0.0  # meters
        self.drift_offset_east = 0.0   # meters
        self.gps_week = 0
        self.skip_params = skip_params
        
    def configure_parameters(self):
        """Configure ArduPilot parameters for GPS spoofing."""
        if self.skip_params:
            print("[*] Skipping parameter configuration (--skip-params enabled)")
            return
        
        print("\n[*] Configuring GPS parameters...")
        
        params = [
            ("GPS2_TYPE", 14, "MAVLink GPS"),
            ("GPS_AUTO_SWITCH", 0, "Use GPS_PRIMARY"),
            ("GPS_PRIMARY", 1, "Use second GPS (GPS2)")
        ]
        # setting params on the SITL
        for param_name, param_value, description in params:
            print(f"  - Setting {param_name} = {param_value} ({description})")
            self.master.mav.param_set_send(
                self.master.target_system,
                self.master.target_component,
                param_name.encode('utf8'),
                param_value,
                mavutil.mavlink.MAV_PARAM_TYPE_INT8
            )
            
            # Wait for ACK (with timeout)
            start_time = time.time()
            ack_received = False
            while time.time() - start_time < 2.0:
                msg = self.master.recv_match(type='PARAM_VALUE', blocking=False)
                if msg:
                    # Handle both bytes and string (pymavlink version compatibility)
                    received_param_id = msg.param_id
                    if isinstance(received_param_id, bytes):
                        received_param_id = received_param_id.decode('utf8').strip('\x00')
                    else:
                        received_param_id = received_param_id.strip('\x00')
                    
                    if received_param_id == param_name:
                        if msg.param_value == param_value:
                            print(f"{param_name} confirmed: {msg.param_value}")
                            ack_received = True
                            break
                time.sleep(0.1)
            
            if not ack_received:
                print(f" Warning: No ACK received for {param_name} (may still be set)")
        
        print("[+] Parameter configuration complete\n")
        time.sleep(1)  # Let parameters settle
        
    def synchronize_with_gps1(self):
        """Read GPS1 position to synchronize spoofed GPS."""
        print("[*] Synchronizing with GPS1...")
        
        timeout = 10.0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = self.master.recv_match(type='GPS_RAW_INT', blocking=True, timeout=1)
            if msg:
                # GPS_RAW_INT doesn't specify instance, assume it's GPS1
                self.gps1_lat = msg.lat / 1e7  # Convert to degrees
                self.gps1_lon = msg.lon / 1e7  # Convert to degrees
                self.gps1_alt = msg.alt / 1000.0  # Convert to meters
                
                print(f"[+] Synchronized with GPS1:")
                print(f"    Lat: {self.gps1_lat:.7f}°")
                print(f"    Lon: {self.gps1_lon:.7f}°")
                print(f"    Alt: {self.gps1_alt:.1f}m MSL")
                print(f"    Fix: Type {msg.fix_type}, Sats: {msg.satellites_visible}")
                
                self.synchronized = True
                self._calculate_gps_time()
                return True
        
        print("[!] ERROR: Failed to synchronize with GPS1 (timeout)")
        return False
    
    def _calculate_gps_time(self):
        """Calculate GPS week and time of week from system time."""
        # GPS epoch: January 6, 1980 00:00:00 UTC
        gps_epoch = datetime(1980, 1, 6, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        delta = now - gps_epoch
        total_seconds = delta.total_seconds()
        
        self.gps_week = int(total_seconds / (7 * 24 * 3600))
        self.gps_time_of_week_ms = int((total_seconds % (7 * 24 * 3600)) * 1000)
    
    def _meters_to_lat_lon_offset(self, north_m, east_m):
        """Convert meter offsets to lat/lon offsets."""
        # Latitude: 1 degree ≈ 111,320 meters (constant)
        lat_offset = north_m / 111320.0
        
        # Longitude: varies with latitude
        # 1 degree lon = 111,320 * cos(lat) meters
        lon_offset = east_m / (111320.0 * math.cos(math.radians(self.gps1_lat)))
        
        return lat_offset, lon_offset
    
    def send_gps_input(self, drift_north_m=0.0, drift_east_m=0.0):
        """Send GPS_INPUT message with optional drift offset."""
        if not self.synchronized:
            print("[!] ERROR: Not synchronized with GPS1")
            return
        
        # Calculate position with drift
        lat_offset, lon_offset = self._meters_to_lat_lon_offset(drift_north_m, drift_east_m)
        spoofed_lat = self.gps1_lat + lat_offset
        spoofed_lon = self.gps1_lon + lon_offset
        
        # Update GPS time
        self._calculate_gps_time()
        
        # Send GPS_INPUT message
        self.master.mav.gps_input_send(
            int(time.time() * 1e6),  # usec timestamp
            GPS_INSTANCE_1,           # gps_id (1 = GPS2)
            0,                        # ignore_flags (0 = use all fields)
            self.gps_time_of_week_ms, # time_week_ms
            self.gps_week,            # time_week
            GPS_FIX_TYPE_3D,          # fix_type (3 = 3D fix)
            int(spoofed_lat * 1e7),   # lat (degrees * 1e7)
            int(spoofed_lon * 1e7),   # lon (degrees * 1e7)
            float(self.gps1_alt),     # alt (meters MSL)
            1.0,                      # hdop 
            1.0,                      # vdop
            0.0,                      # vn (velocity north, m/s)
            0.0,                      # ve (velocity east, m/s)
            0.0,                      # vd (velocity down, m/s)
            0.5,                      # speed_accuracy (m/s)
            1.0,                      # horiz_accuracy (meters)
            2.0,                      # vert_accuracy (meters)
            12,                       # satellites_visible
            0                         # yaw (cdeg, 0 = not used)
        )
    
    def run_drift_experiment(self, drift_rate_m_s, drift_direction_deg, drift_delay_s, duration_s):
        """Run the GPS drift spoofing experiment."""
        print(f"\n[*] Starting GPS Drift Experiment")
        print(f"    Drift Rate: {drift_rate_m_s} m/s")
        print(f"    Drift Direction: {drift_direction_deg}° (0=North, 90=East)")
        print(f"    Drift Delay: {drift_delay_s}s")
        print(f"    Total Duration: {duration_s}s\n")
        
        # Calculate drift components
        drift_north_rate = drift_rate_m_s * math.cos(math.radians(drift_direction_deg))
        drift_east_rate = drift_rate_m_s * math.sin(math.radians(drift_direction_deg))
        
        start_time = time.time()
        last_print_time = start_time
        drift_started = False
        
        print("[*] Sending GPS_INPUT at 1 Hz...")
        print("    (Initial position matches GPS1)")
        
        try:
            while time.time() - start_time < duration_s:
                elapsed = time.time() - start_time
                
                # Start drift after delay
                if elapsed >= drift_delay_s and not drift_started:
                    print(f"\n[!] DRIFT PHASE STARTED (after {drift_delay_s}s)")
                    drift_started = True
                
                # Calculate cumulative drift
                if drift_started:
                    drift_time = elapsed - drift_delay_s
                    self.drift_offset_north = drift_north_rate * drift_time
                    self.drift_offset_east = drift_east_rate * drift_time
                else:
                    self.drift_offset_north = 0.0
                    self.drift_offset_east = 0.0
                
                # Send GPS_INPUT
                self.send_gps_input(self.drift_offset_north, self.drift_offset_east)
                
                # Print status every second
                if time.time() - last_print_time >= 1.0:
                    total_drift = math.sqrt(self.drift_offset_north**2 + self.drift_offset_east**2)
                    if drift_started:
                        print(f"  [{int(elapsed)}s] Drift: {total_drift:.1f}m (N:{self.drift_offset_north:.1f}m, E:{self.drift_offset_east:.1f}m)")
                    else:
                        print(f"  [{int(elapsed)}s] Synced at GPS1 position (waiting for drift phase...)")
                    last_print_time = time.time()
                
                # 1 Hz update rate
                time.sleep(1.0)
        
        except KeyboardInterrupt:
            print("\n[!] Experiment interrupted by user")
        
        total_drift = math.sqrt(self.drift_offset_north**2 + self.drift_offset_east**2)
        print(f"\n[+] Experiment complete!")
        print(f"    Total drift: {total_drift:.1f}m")
        print(f"    Final offset: N:{self.drift_offset_north:.1f}m, E:{self.drift_offset_east:.1f}m")


def main():
    parser = argparse.ArgumentParser(
        description="GPS Spoofing Script - Subtle Drift Experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--connection', default='udpin:127.0.0.1:14551',
                        help='MAVLink connection string (default: udpin:127.0.0.1:14551)')
    parser.add_argument('--drift-rate', type=float, default=0.5,
                        help='Drift rate in m/s (default: 0.5)')
    parser.add_argument('--drift-direction', type=float, default=0.0,
                        help='Drift direction in degrees, 0=North, 90=East (default: 0)')
    parser.add_argument('--drift-delay', type=float, default=10.0,
                        help='Seconds to wait before starting drift (default: 10)')
    parser.add_argument('--duration', type=float, default=120.0,
                        help='Total experiment duration in seconds (default: 120)')
    parser.add_argument('--skip-params', action='store_true',
                        help='Skip parameter configuration (assume manual setup)')
    
    args = parser.parse_args()
    
    # Create GPS spoofing instance
    gps_spoof = GPSSpoofing(args.connection, skip_params=args.skip_params)
    
    # Configure parameters
    gps_spoof.configure_parameters()
    
    # Synchronize with GPS1
    if not gps_spoof.synchronize_with_gps1():
        print("[!] Failed to start experiment")
        sys.exit(1)
    
    # Run drift experiment
    gps_spoof.run_drift_experiment(
        drift_rate_m_s=args.drift_rate,
        drift_direction_deg=args.drift_direction,
        drift_delay_s=args.drift_delay,
        duration_s=args.duration
    )


if __name__ == "__main__":
    main()
