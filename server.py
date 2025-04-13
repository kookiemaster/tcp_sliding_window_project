#!/usr/bin/env python3
"""
TCP Sliding Window Protocol - Server Implementation
CS 258 Project Assignment

Author: Xiangyi Li (xiangyi@benchflow.ai)

This server implementation:
1. Listens for TCP connections from clients
2. Receives sequence numbers from the client
3. Tracks missing sequence numbers
4. Sends ACK numbers back to the client
5. Calculates and reports goodput statistics
"""

import socket
import time
import json
import threading
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TCP-Server')

class TCPServer:
    """
    TCP Server implementing sliding window protocol receiver functionality.
    """
    
    def __init__(self, host='0.0.0.0', port=12345, max_seq_num=2**16):
        """
        Initialize the TCP server.
        
        Args:
            host (str): Host address to bind to
            port (int): Port number to bind to
            max_seq_num (int): Maximum sequence number (default: 2^16)
        """
        self.host = host
        self.port = port
        self.max_seq_num = max_seq_num
        
        # Socket setup
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Data structures for tracking packets
        self.received_packets = set()  # Set of received sequence numbers
        self.missing_packets = set()   # Set of missing sequence numbers
        self.highest_seq_received = -1  # Highest sequence number received
        
        # Statistics
        self.total_packets_received = 0
        self.total_packets_expected = 0
        self.goodput_measurements = []  # List to store goodput measurements
        self.measurement_timestamps = []  # Timestamps for measurements
        
        # Window size tracking for visualization
        self.window_sizes = []  # List to store window sizes over time
        self.window_timestamps = []  # Timestamps for window size measurements
        
        # Sequence number tracking for visualization
        self.seq_nums_received = []  # List of sequence numbers received over time
        self.seq_nums_dropped = []   # List of sequence numbers dropped over time
        self.seq_timestamps = []     # Timestamps for sequence number tracking
        
        # Retransmission statistics
        self.retransmission_stats = defaultdict(int)  # {seq_num: retransmission_count}
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Client information
        self.client_address = None
    
    def start(self):
        """
        Start the TCP server and listen for connections.
        """
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            logger.info(f"Server started on {self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.server_socket.accept()
                self.client_address = client_address
                logger.info(f"Connection established with {client_address}")
                
                # Handle client connection in a new thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            self.server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        """
        Handle client connection and implement the sliding window protocol.
        
        Args:
            client_socket (socket): Socket object for client connection
            client_address (tuple): Client address information (ip, port)
        """
        try:
            # Send connection setup success message
            client_socket.send("Connection setup success".encode())
            
            # Start time for statistics
            start_time = time.time()
            last_measurement_time = start_time
            
            while True:
                # Receive data from client
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse received data
                try:
                    message = json.loads(data.decode())
                    seq_num = message.get('seq_num')
                    window_size = message.get('window_size', 0)
                    
                    # Process the sequence number
                    with self.lock:
                        self.process_sequence_number(seq_num)
                        
                        # Track window size for visualization
                        current_time = time.time() - start_time
                        self.window_sizes.append(window_size)
                        self.window_timestamps.append(current_time)
                        
                        # Calculate and record goodput periodically (every 1000 packets)
                        if self.total_packets_received % 1000 == 0 and self.total_packets_received > 0:
                            goodput = len(self.received_packets) / self.total_packets_expected
                            self.goodput_measurements.append(goodput)
                            self.measurement_timestamps.append(current_time)
                            logger.info(f"Goodput after {self.total_packets_received} packets: {goodput:.4f}")
                    
                    # Send ACK back to client
                    ack_message = json.dumps({'ack_num': seq_num + 1})
                    client_socket.send(ack_message.encode())
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON data received")
                except Exception as e:
                    logger.error(f"Error processing data: {e}")
        
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
            logger.info(f"Connection with {client_address} closed")
            
            # Calculate final statistics
            self.calculate_final_statistics()
    
    def process_sequence_number(self, seq_num):
        """
        Process a received sequence number.
        
        Args:
            seq_num (int): The sequence number received from client
        """
        # Update statistics
        self.total_packets_expected += 1
        
        # Check if this is a new sequence number or a retransmission
        if seq_num in self.received_packets:
            # This is a retransmission
            self.retransmission_stats[seq_num] += 1
        else:
            # This is a new sequence number
            self.total_packets_received += 1
            self.received_packets.add(seq_num)
            
            # Track sequence numbers for visualization
            current_time = time.time()
            self.seq_nums_received.append(seq_num)
            self.seq_timestamps.append(current_time)
            
            # Update highest sequence number received
            if seq_num > self.highest_seq_received:
                # Check for missing packets
                for i in range(self.highest_seq_received + 1, seq_num):
                    if i not in self.received_packets and i not in self.missing_packets:
                        self.missing_packets.add(i)
                        # Track dropped packets for visualization
                        self.seq_nums_dropped.append(i)
                
                self.highest_seq_received = seq_num
    
    def calculate_final_statistics(self):
        """
        Calculate and log final statistics.
        """
        if self.total_packets_expected == 0:
            logger.warning("No packets were processed")
            return
        
        final_goodput = len(self.received_packets) / self.total_packets_expected
        
        logger.info("=== Final Statistics ===")
        logger.info(f"Total packets expected: {self.total_packets_expected}")
        logger.info(f"Total packets received: {self.total_packets_received}")
        logger.info(f"Missing packets: {len(self.missing_packets)}")
        logger.info(f"Final goodput: {final_goodput:.4f}")
        logger.info(f"Number of retransmissions: {sum(self.retransmission_stats.values())}")
    
    def get_statistics(self):
        """
        Get server statistics for visualization and reporting.
        
        Returns:
            dict: Dictionary containing server statistics
        """
        with self.lock:
            stats = {
                'server_address': f"{self.host}:{self.port}",
                'client_address': self.client_address,
                'total_packets_expected': self.total_packets_expected,
                'total_packets_received': self.total_packets_received,
                'missing_packets': len(self.missing_packets),
                'goodput_measurements': self.goodput_measurements,
                'measurement_timestamps': self.measurement_timestamps,
                'window_sizes': self.window_sizes,
                'window_timestamps': self.window_timestamps,
                'seq_nums_received': self.seq_nums_received,
                'seq_nums_dropped': self.seq_nums_dropped,
                'seq_timestamps': self.seq_timestamps,
                'retransmission_stats': dict(self.retransmission_stats)
            }
        
        return stats

def main():
    """
    Main function to start the TCP server.
    """
    # Create and start the server
    server = TCPServer()
    server.start()

if __name__ == "__main__":
    main()
