#!/usr/bin/env python3
"""
Simplified Test Script for TCP Sliding Window Protocol
CS 258 Project Assignment

Author: Xiangyi Li (xiangyi@benchflow.ai)

This simplified test script:
1. Creates mock data for visualization
2. Generates visualizations using the visualizer module
"""

import os
import json
import random
import time
import numpy as np
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TCP-Test-Simplified')

class MockDataGenerator:
    """
    Generate mock data for testing visualization
    """
    
    def __init__(self, output_dir='./output'):
        """
        Initialize the mock data generator
        
        Args:
            output_dir (str): Directory to save output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Statistics files
        self.server_stats_file = os.path.join(output_dir, 'server_stats.json')
        self.client_stats_file = os.path.join(output_dir, 'client_stats.json')
    
    def generate_client_stats(self, total_packets=1000):
        """
        Generate mock client statistics
        
        Args:
            total_packets (int): Total number of packets to simulate
            
        Returns:
            dict: Client statistics
        """
        # Initialize statistics
        window_sizes = []
        window_timestamps = []
        retransmission_counts = {}
        
        # Generate window size data
        current_window = 10
        for i in range(total_packets):
            # Randomly adjust window size
            if random.random() < 0.1:
                current_window = max(5, min(100, current_window + random.randint(-3, 5)))
            
            window_sizes.append(current_window)
            window_timestamps.append(i * 0.01)  # Simulate time passing
        
        # Generate retransmission data
        total_dropped = int(total_packets * 0.01)  # 1% drop rate
        total_retransmitted = total_dropped
        
        # Create retransmission counts
        for i in range(1, 5):  # 1 to 4 retransmissions
            count = int(total_dropped * (0.7 ** (i-1)))  # Decreasing probability
            for j in range(count):
                seq_num = random.randint(0, total_packets-1)
                retransmission_counts[str(seq_num)] = i
        
        # Create client statistics
        client_stats = {
            'client_address': '127.0.0.1:54321',
            'server_address': '127.0.0.1:12345',
            'total_sent': total_packets,
            'total_dropped': total_dropped,
            'total_retransmitted': total_retransmitted,
            'total_acked': total_packets - total_dropped + total_retransmitted,
            'window_sizes': window_sizes,
            'window_timestamps': window_timestamps,
            'retransmission_counts': retransmission_counts
        }
        
        # Save to file
        with open(self.client_stats_file, 'w') as f:
            json.dump(client_stats, f, indent=4)
        
        logger.info(f"Mock client statistics saved to {self.client_stats_file}")
        return client_stats
    
    def generate_server_stats(self, total_packets=1000):
        """
        Generate mock server statistics
        
        Args:
            total_packets (int): Total number of packets to simulate
            
        Returns:
            dict: Server statistics
        """
        # Initialize statistics
        goodput_measurements = []
        measurement_timestamps = []
        seq_nums_received = []
        seq_nums_dropped = []
        seq_timestamps = []
        
        # Generate goodput data
        for i in range(0, total_packets, 100):
            # Calculate goodput (slightly decreasing over time)
            goodput = 0.99 - (i / total_packets) * 0.05 + random.uniform(-0.01, 0.01)
            goodput_measurements.append(goodput)
            measurement_timestamps.append(i * 0.01)
        
        # Generate sequence number data
        for i in range(total_packets):
            if random.random() < 0.99:  # 99% success rate
                seq_nums_received.append(i)
                seq_timestamps.append(i * 0.01)
            else:
                seq_nums_dropped.append(i)
        
        # Create server statistics
        server_stats = {
            'server_address': '127.0.0.1:12345',
            'client_address': ('127.0.0.1', 54321),
            'total_packets_expected': total_packets,
            'total_packets_received': len(seq_nums_received),
            'missing_packets': len(seq_nums_dropped),
            'goodput_measurements': goodput_measurements,
            'measurement_timestamps': measurement_timestamps,
            'window_sizes': [],  # Server doesn't track window sizes
            'window_timestamps': [],
            'seq_nums_received': seq_nums_received,
            'seq_nums_dropped': seq_nums_dropped,
            'seq_timestamps': seq_timestamps,
            'retransmission_stats': {}
        }
        
        # Save to file
        with open(self.server_stats_file, 'w') as f:
            json.dump(server_stats, f, indent=4)
        
        logger.info(f"Mock server statistics saved to {self.server_stats_file}")
        return server_stats
    
    def generate_visualizations(self):
        """
        Generate visualizations using the visualizer module
        
        Returns:
            bool: True if visualizations generated successfully, False otherwise
        """
        try:
            # Run the visualizer
            logger.info("Generating visualizations...")
            visualizer_process = subprocess.run(
                [
                    sys.executable, 
                    'visualizer.py',
                    '--client', self.client_stats_file,
                    '--server', self.server_stats_file,
                    '--output', self.output_dir
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if visualizer_process.returncode != 0:
                logger.error(f"Visualizer failed: {visualizer_process.stderr}")
                return False
            
            logger.info("Visualizations generated successfully")
            logger.info(visualizer_process.stdout)
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            return False

def main():
    """
    Main function to run the mock data generator
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TCP Sliding Window Protocol Mock Data Generator')
    parser.add_argument('--packets', type=int, default=1000, 
                        help='Total packets to simulate')
    parser.add_argument('--output', default='./output', 
                        help='Output directory for test results')
    
    args = parser.parse_args()
    
    # Create generator
    generator = MockDataGenerator(output_dir=args.output)
    
    # Generate mock data
    generator.generate_client_stats(total_packets=args.packets)
    generator.generate_server_stats(total_packets=args.packets)
    
    # Generate visualizations
    if generator.generate_visualizations():
        print("Mock data and visualizations generated successfully")
        print(f"Results saved to {args.output}/")
    else:
        print("Failed to generate visualizations")

if __name__ == "__main__":
    main()
