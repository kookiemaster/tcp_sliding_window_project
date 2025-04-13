#!/usr/bin/env python3
"""
TCP Sliding Window Protocol - Test Script
CS 258 Project Assignment

Author: Xiangyi Li (xiangyi@benchflow.ai)

This test script:
1. Runs the server in a separate process
2. Runs the client in a separate process with reduced packet count for testing
3. Collects statistics from both server and client
4. Generates visualizations using the visualizer module
"""

import os
import sys
import time
import json
import subprocess
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TCP-Test')

class TCPTester:
    """
    Test class for TCP sliding window protocol implementation.
    """
    
    def __init__(self, output_dir='./output'):
        """
        Initialize the TCP tester.
        
        Args:
            output_dir (str): Directory to save test outputs
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process handles
        self.server_process = None
        self.client_process = None
        
        # Statistics files
        self.server_stats_file = os.path.join(output_dir, 'server_stats.json')
        self.client_stats_file = os.path.join(output_dir, 'client_stats.json')
    
    def start_server(self):
        """
        Start the TCP server in a separate process.
        
        Returns:
            bool: True if server started successfully, False otherwise
        """
        try:
            # Create a modified version of server.py that saves statistics
            self.create_test_server_script()
            
            # Start the server process
            logger.info("Starting server...")
            self.server_process = subprocess.Popen(
                [sys.executable, os.path.join(self.output_dir, 'test_server.py')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(2)
            
            if self.server_process.poll() is not None:
                # Server process exited
                stdout, stderr = self.server_process.communicate()
                logger.error(f"Server failed to start: {stderr}")
                return False
            
            logger.info("Server started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def start_client(self, total_packets=10000):
        """
        Start the TCP client in a separate process.
        
        Args:
            total_packets (int): Total number of packets to send (reduced for testing)
            
        Returns:
            bool: True if client started successfully, False otherwise
        """
        try:
            # Create a modified version of client.py that saves statistics
            self.create_test_client_script()
            
            # Start the client process
            logger.info(f"Starting client with {total_packets} packets...")
            self.client_process = subprocess.Popen(
                [
                    sys.executable, 
                    os.path.join(self.output_dir, 'test_client.py'),
                    '--packets', str(total_packets)
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for client to start
            time.sleep(2)
            
            if self.client_process.poll() is not None:
                # Client process exited
                stdout, stderr = self.client_process.communicate()
                logger.error(f"Client failed to start: {stderr}")
                return False
            
            logger.info("Client started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting client: {e}")
            return False
    
    def create_test_server_script(self):
        """
        Create a modified version of server.py that saves statistics.
        """
        # Read the original server.py
        with open('server.py', 'r') as f:
            server_code = f.read()
        
        # Add code to save statistics
        save_stats_code = f"""
# Save statistics to file
def save_statistics(server):
    stats = server.get_statistics()
    with open('{self.server_stats_file}', 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Server statistics saved to {self.server_stats_file}")

# Modify main function to save statistics
def main():
    # Create and start the server
    server = TCPServer()
    
    # Register signal handler to save statistics on exit
    def signal_handler(sig, frame):
        print("Saving statistics before exit...")
        save_statistics(server)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server.start()
    except KeyboardInterrupt:
        save_statistics(server)
    finally:
        save_statistics(server)

if __name__ == "__main__":
    main()
"""
        
        # Replace the original main function
        modified_server_code = server_code.replace(
            "def main():\n    \"\"\"\n    Main function to start the TCP server.\n    \"\"\"\n    # Create and start the server\n    server = TCPServer()\n    server.start()\n\nif __name__ == \"__main__\":\n    main()",
            save_stats_code
        )
        
        # Add import for signal module
        if "import signal" not in modified_server_code:
            modified_server_code = modified_server_code.replace(
                "import logging",
                "import logging\nimport signal"
            )
        
        # Write the modified server code to a new file
        with open(os.path.join(self.output_dir, 'test_server.py'), 'w') as f:
            f.write(modified_server_code)
    
    def create_test_client_script(self):
        """
        Create a modified version of client.py that saves statistics.
        """
        # Read the original client.py
        with open('client.py', 'r') as f:
            client_code = f.read()
        
        # Add code to save statistics
        save_stats_code = f"""
# Save statistics to file
def save_statistics(client):
    stats = client.get_statistics()
    with open('{self.client_stats_file}', 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Client statistics saved to {self.client_stats_file}")

# Modify main function to save statistics
def main():
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TCP Sliding Window Protocol Client')
    parser.add_argument('--host', default='localhost', help='Server hostname or IP address')
    parser.add_argument('--port', type=int, default=12345, help='Server port number')
    parser.add_argument('--window', type=int, default=10, help='Initial window size')
    parser.add_argument('--drop', type=float, default=0.01, help='Packet drop probability')
    parser.add_argument('--retransmit', type=int, default=100, 
                        help='Retransmit after this many sequence numbers')
    parser.add_argument('--packets', type=int, default=10000000, help='Total packets to send')
    
    args = parser.parse_args()
    
    # Create and start the client
    client = TCPClient(
        server_host=args.host,
        server_port=args.port,
        window_size=args.window,
        drop_probability=args.drop,
        retransmit_after=args.retransmit,
        total_packets=args.packets
    )
    
    # Register signal handler to save statistics on exit
    def signal_handler(sig, frame):
        print("Saving statistics before exit...")
        save_statistics(client)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        client.start()
    except KeyboardInterrupt:
        save_statistics(client)
    finally:
        save_statistics(client)

if __name__ == "__main__":
    main()
"""
        
        # Replace the original main function
        modified_client_code = client_code.replace(
            "def main():\n    \"\"\"\n    Main function to start the TCP client.\n    \"\"\"\n    import argparse\n    \n    # Parse command line arguments\n    parser = argparse.ArgumentParser(description='TCP Sliding Window Protocol Client')\n    parser.add_argument('--host', default='localhost', help='Server hostname or IP address')\n    parser.add_argument('--port', type=int, default=12345, help='Server port number')\n    parser.add_argument('--window', type=int, default=10, help='Initial window size')\n    parser.add_argument('--drop', type=float, default=0.01, help='Packet drop probability')\n    parser.add_argument('--retransmit', type=int, default=100, \n                        help='Retransmit after this many sequence numbers')\n    parser.add_argument('--packets', type=int, default=10000000, help='Total packets to send')\n    \n    args = parser.parse_args()\n    \n    # Create and start the client\n    client = TCPClient(\n        server_host=args.host,\n        server_port=args.port,\n        window_size=args.window,\n        drop_probability=args.drop,\n        retransmit_after=args.retransmit,\n        total_packets=args.packets\n    )\n    \n    client.start()\n\nif __name__ == \"__main__\":\n    main()",
            save_stats_code
        )
        
        # Add import for signal module
        if "import signal" not in modified_client_code:
            modified_client_code = modified_client_code.replace(
                "import logging",
                "import logging\nimport signal"
            )
        
        # Write the modified client code to a new file
        with open(os.path.join(self.output_dir, 'test_client.py'), 'w') as f:
            f.write(modified_client_code)
    
    def run_test(self, total_packets=10000, timeout=300):
        """
        Run a complete test of the TCP sliding window protocol.
        
        Args:
            total_packets (int): Total number of packets to send (reduced for testing)
            timeout (int): Maximum time to wait for test completion in seconds
            
        Returns:
            bool: True if test completed successfully, False otherwise
        """
        try:
            # Start server
            if not self.start_server():
                return False
            
            # Start client
            if not self.start_client(total_packets):
                self.stop_server()
                return False
            
            # Wait for client to complete
            logger.info(f"Test running with {total_packets} packets (timeout: {timeout}s)...")
            start_time = time.time()
            
            while self.client_process.poll() is None:
                # Check if timeout exceeded
                if time.time() - start_time > timeout:
                    logger.warning(f"Test timeout exceeded ({timeout}s)")
                    break
                
                # Wait a bit
                time.sleep(5)
                logger.info("Test still running...")
            
            # Get client output
            client_stdout, client_stderr = self.client_process.communicate()
            
            if client_stderr:
                logger.warning(f"Client stderr: {client_stderr}")
            
            # Stop server
            self.stop_server()
            
            # Check if statistics files were created
            if not os.path.exists(self.server_stats_file):
                logger.error("Server statistics file not created")
                return False
            
            if not os.path.exists(self.client_stats_file):
                logger.error("Client statistics file not created")
                return False
            
            logger.info("Test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running test: {e}")
            self.stop_server()
            self.stop_client()
            return False
    
    def stop_server(self):
        """
        Stop the TCP server process.
        """
        if self.server_process is not None:
            logger.info("Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
    
    def stop_client(self):
        """
        Stop the TCP client process.
        """
        if self.client_process is not None:
            logger.info("Stopping client...")
            self.client_process.terminate()
            try:
                self.client_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.client_process.kill()
            self.client_process = None
    
    def generate_visualizations(self):
        """
        Generate visualizations using the visualizer module.
        
        Returns:
            bool: True if visualizations generated successfully, False otherwise
        """
        try:
            # Check if statistics files exist
            if not os.path.exists(self.server_stats_file):
                logger.error("Server statistics file not found")
                return False
            
            if not os.path.exists(self.client_stats_file):
                logger.error("Client statistics file not found")
                return False
            
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
    Main function to run the TCP tester.
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TCP Sliding Window Protocol Tester')
    parser.add_argument('--packets', type=int, default=10000, 
                        help='Total packets to send (reduced for testing)')
    parser.add_argument('--timeout', type=int, default=300, 
                        help='Maximum time to wait for test completion in seconds')
    parser.add_argument('--output', default='./output', 
                        help='Output directory for test results')
    
    args = parser.parse_args()
    
    # Create tester
    tester = TCPTester(output_dir=args.output)
    
    # Run test
    if tester.run_test(total_packets=args.packets, timeout=args.timeout):
        # Generate visualizations
        tester.generate_visualizations()
        
        print("Test completed successfully")
        print(f"Results saved to {args.output}/")
    else:
        print("Test failed")

if __name__ == "__main__":
    main()
