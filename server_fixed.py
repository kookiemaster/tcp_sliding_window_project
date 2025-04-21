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
import os
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TCP-Server')

class TCPServer:
    """
    TCP Server implementing sliding window protocol.
    """
    
    def __init__(self, host='0.0.0.0', port=12345, max_seq_num=2**16):
        """
        Initialize the TCP server.
        
        Args:
            host (str): Host address to bind the server
            port (int): Port number to bind the server
            max_seq_num (int): Maximum sequence number
        """
        self.host = host
        self.port = port
        self.max_seq_num = max_seq_num
        self.server_socket = None
        
        # Data structures for tracking packets
        self.received_packets = set()
        self.missing_packets = set()
        self.highest_seq_num = -1
        self.total_packets_received = 0
        self.total_packets_expected = 0
        
        # Statistics for visualization
        self.window_sizes = []
        self.window_timestamps = []
        self.seq_nums_received = []
        self.seq_nums_timestamps = []
        self.seq_nums_dropped = []
        self.goodput_measurements = []
        self.goodput_timestamps = []
        
        # Thread synchronization
        self.lock = threading.Lock()
        
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
    
    def start(self):
        """
        Start the TCP server and listen for connections.
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            logger.info(f"Server started on {self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"Connection established with {client_address}")
                
                # Start a new thread to handle the client
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
            # First, receive the initial string from client
            initial_data = client_socket.recv(4096)
            if not initial_data:
                logger.error("No initial data received from client")
                return
                
            initial_message = initial_data.decode()
            logger.info(f"Received initial message: {initial_message}")
            
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
                            self.goodput_timestamps.append(current_time)
                            logger.info(f"Goodput: {goodput:.4f} ({len(self.received_packets)}/{self.total_packets_expected})")
                    
                    # Send ACK back to client
                    ack_message = json.dumps({'ack': seq_num})
                    client_socket.send(ack_message.encode())
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON data received")
                except Exception as e:
                    logger.error(f"Error processing data: {e}")
            
            # Calculate final statistics
            self.calculate_final_statistics()
            
            # Save statistics to file
            self.save_statistics(client_address)
            
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
            logger.info(f"Connection closed with {client_address}")
    
    def process_sequence_number(self, seq_num):
        """
        Process received sequence number and track missing packets.
        
        Args:
            seq_num (int): Received sequence number
        """
        if seq_num is None:
            return
        
        # Record sequence number and timestamp
        current_time = time.time()
        self.seq_nums_received.append(seq_num)
        self.seq_nums_timestamps.append(current_time)
        
        # Add to received packets set
        self.received_packets.add(seq_num)
        self.total_packets_received += 1
        
        # Update highest sequence number
        if seq_num > self.highest_seq_num:
            # Update expected packets count
            self.total_packets_expected = seq_num + 1
            
            # Check for missing packets
            for i in range(self.highest_seq_num + 1, seq_num):
                if i not in self.received_packets:
                    self.missing_packets.add(i)
                    self.seq_nums_dropped.append(i)
            
            self.highest_seq_num = seq_num
    
    def calculate_final_statistics(self):
        """
        Calculate final statistics after connection is closed.
        """
        if self.total_packets_expected == 0:
            return
        
        # Calculate final goodput
        final_goodput = len(self.received_packets) / self.total_packets_expected
        logger.info(f"Final goodput: {final_goodput:.4f} ({len(self.received_packets)}/{self.total_packets_expected})")
        
        # Calculate average goodput
        if self.goodput_measurements:
            avg_goodput = sum(self.goodput_measurements) / len(self.goodput_measurements)
            logger.info(f"Average goodput: {avg_goodput:.4f}")
    
    def get_statistics(self):
        """
        Get server statistics.
        
        Returns:
            dict: Server statistics
        """
        return {
            'received_packets': len(self.received_packets),
            'missing_packets': len(self.missing_packets),
            'total_packets_received': self.total_packets_received,
            'total_packets_expected': self.total_packets_expected,
            'highest_seq_num': self.highest_seq_num,
            'window_sizes': self.window_sizes,
            'window_timestamps': self.window_timestamps,
            'seq_nums_received': self.seq_nums_received,
            'seq_nums_timestamps': self.seq_nums_timestamps,
            'seq_nums_dropped': self.seq_nums_dropped,
            'goodput_measurements': self.goodput_measurements,
            'goodput_timestamps': self.goodput_timestamps
        }
    
    def save_statistics(self, client_address):
        """
        Save server statistics to file.
        
        Args:
            client_address (tuple): Client address information (ip, port)
        """
        stats = self.get_statistics()
        stats['client_address'] = client_address
        stats['server_address'] = (self.host, self.port)
        
        with open('output/server_stats.json', 'w') as f:
            json.dump(stats, f, indent=4)
        
        logger.info("Server statistics saved to output/server_stats.json")

def main():
    """
    Main function to start the TCP server.
    """
    server = TCPServer()
    server.start()

if __name__ == "__main__":
    main()
