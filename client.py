#!/usr/bin/env python3
"""
TCP Sliding Window Protocol - Client Implementation
CS 258 Project Assignment

Author: Xiangyi Li (xiangyi@benchflow.ai)

This client implementation:
1. Connects to the TCP server
2. Sends sequence numbers to the server using sliding window protocol
3. Probabilistically drops 1% of packets
4. Retransmits dropped packets after a specific time
5. Adjusts sliding window based on received ACKs
"""

import socket
import time
import json
import random
import logging
import threading
from collections import deque, defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TCP-Client')

class TCPClient:
    """
    TCP Client implementing sliding window protocol sender functionality.
    """
    
    def __init__(self, server_host='localhost', server_port=12345, 
                 window_size=10, drop_probability=0.01, 
                 retransmit_after=100, max_seq_num=2**16, 
                 total_packets=10000000):
        """
        Initialize the TCP client.
        
        Args:
            server_host (str): Server hostname or IP address
            server_port (int): Server port number
            window_size (int): Initial sliding window size
            drop_probability (float): Probability of packet drop (0.01 = 1%)
            retransmit_after (int): Number of sequence numbers after which to retransmit
            max_seq_num (int): Maximum sequence number (default: 2^16)
            total_packets (int): Total number of packets to send
        """
        self.server_host = server_host
        self.server_port = server_port
        self.window_size = window_size
        self.drop_probability = drop_probability
        self.retransmit_after = retransmit_after
        self.max_seq_num = max_seq_num
        self.total_packets = total_packets
        
        # Socket setup
        self.client_socket = None
        
        # Sliding window variables
        self.base = 0  # Base of the window
        self.next_seq_num = 0  # Next sequence number to be sent
        
        # Packet tracking
        self.sent_packets = set()  # Set of sent sequence numbers
        self.acked_packets = set()  # Set of acknowledged sequence numbers
        self.dropped_packets = set()  # Set of dropped sequence numbers
        self.packets_to_retransmit = deque()  # Queue of packets to retransmit
        
        # Statistics
        self.total_sent = 0
        self.total_dropped = 0
        self.total_retransmitted = 0
        
        # Window size tracking for visualization
        self.window_sizes = []  # List to store window sizes over time
        self.window_timestamps = []  # Timestamps for window size measurements
        
        # Retransmission statistics
        self.retransmission_counts = defaultdict(int)  # {seq_num: retransmission_count}
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Flag to control threads
        self.running = False
    
    def connect(self):
        """
        Connect to the TCP server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            
            # Send initial string to server
            self.client_socket.send("network".encode())
            
            # Receive connection setup success message
            response = self.client_socket.recv(1024).decode()
            logger.info(f"Server response: {response}")
            
            if "success" in response.lower():
                logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
                return True
            else:
                logger.error("Connection setup failed")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def start(self):
        """
        Start the TCP client and begin sending packets.
        """
        if not self.connect():
            return
        
        self.running = True
        
        # Start thread to receive ACKs
        ack_thread = threading.Thread(target=self.receive_acks)
        ack_thread.daemon = True
        ack_thread.start()
        
        # Start thread to handle retransmissions
        retransmit_thread = threading.Thread(target=self.handle_retransmissions)
        retransmit_thread.daemon = True
        retransmit_thread.start()
        
        # Start sending packets
        start_time = time.time()
        
        try:
            while self.total_sent < self.total_packets and self.running:
                with self.lock:
                    # Check if window is full
                    if self.next_seq_num < self.base + self.window_size and self.next_seq_num < self.total_packets:
                        # Send the next packet
                        self.send_packet(self.next_seq_num)
                        self.next_seq_num += 1
                        
                        # Record window size for visualization
                        current_time = time.time() - start_time
                        self.window_sizes.append(self.window_size)
                        self.window_timestamps.append(current_time)
                
                # Sleep to prevent CPU overload
                time.sleep(0.001)
            
            # Wait for all packets to be acknowledged
            while len(self.acked_packets) < self.total_packets and self.running:
                logger.info(f"Waiting for remaining ACKs... {len(self.acked_packets)}/{self.total_packets}")
                time.sleep(1)
            
            logger.info("All packets sent and acknowledged")
            
        except KeyboardInterrupt:
            logger.info("Client shutting down...")
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            self.running = False
            if self.client_socket:
                self.client_socket.close()
            
            # Calculate and display final statistics
            self.calculate_final_statistics()
    
    def send_packet(self, seq_num):
        """
        Send a packet (sequence number) to the server.
        
        Args:
            seq_num (int): Sequence number to send
        """
        # Check if we should drop this packet
        should_drop = random.random() < self.drop_probability
        
        if should_drop:
            # Simulate packet drop
            logger.debug(f"Dropping packet with seq_num {seq_num}")
            self.dropped_packets.add(seq_num)
            self.total_dropped += 1
            
            # Schedule for retransmission
            self.packets_to_retransmit.append((seq_num, self.next_seq_num + self.retransmit_after))
        else:
            # Send the packet
            try:
                message = json.dumps({
                    'seq_num': seq_num,
                    'window_size': self.window_size
                })
                self.client_socket.send(message.encode())
                self.sent_packets.add(seq_num)
                self.total_sent += 1
                
                if seq_num % 1000 == 0:
                    logger.info(f"Sent packet with seq_num {seq_num}")
            
            except Exception as e:
                logger.error(f"Error sending packet: {e}")
    
    def receive_acks(self):
        """
        Continuously receive ACKs from the server and adjust the sliding window.
        """
        while self.running:
            try:
                # Receive ACK from server
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                # Parse ACK
                message = json.loads(data.decode())
                ack_num = message.get('ack_num')
                
                if ack_num is not None:
                    with self.lock:
                        # The ACK number is the next expected sequence number
                        seq_num = ack_num - 1
                        
                        # Mark packet as acknowledged
                        if seq_num not in self.acked_packets:
                            self.acked_packets.add(seq_num)
                            
                            # If this was the base of the window, move the window forward
                            if seq_num == self.base:
                                # Find the new base (next unacknowledged packet)
                                while self.base in self.acked_packets and self.base < self.next_seq_num:
                                    self.base += 1
                                
                                # Increase window size (simple congestion control)
                                if self.window_size < 100:  # Maximum window size
                                    self.window_size += 1
                            
                            if seq_num % 1000 == 0:
                                logger.info(f"Received ACK for seq_num {seq_num}, window: [{self.base}, {self.base + self.window_size})")
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON data received")
            except Exception as e:
                logger.error(f"Error receiving ACK: {e}")
                break
    
    def handle_retransmissions(self):
        """
        Handle retransmission of dropped packets.
        """
        while self.running:
            try:
                with self.lock:
                    # Check if there are packets to retransmit
                    if self.packets_to_retransmit:
                        seq_num, retransmit_after = self.packets_to_retransmit[0]
                        
                        # Check if it's time to retransmit
                        if retransmit_after <= self.next_seq_num:
                            # Remove from queue
                            self.packets_to_retransmit.popleft()
                            
                            # Check if already acknowledged
                            if seq_num not in self.acked_packets:
                                # Retransmit with same drop probability
                                should_drop = random.random() < self.drop_probability
                                
                                if should_drop:
                                    # Packet dropped again, reschedule
                                    logger.debug(f"Retransmission of seq_num {seq_num} dropped again")
                                    self.packets_to_retransmit.append((seq_num, self.next_seq_num + self.retransmit_after))
                                else:
                                    # Retransmit the packet
                                    logger.debug(f"Retransmitting seq_num {seq_num}")
                                    message = json.dumps({
                                        'seq_num': seq_num,
                                        'window_size': self.window_size
                                    })
                                    self.client_socket.send(message.encode())
                                    self.total_retransmitted += 1
                                    
                                    # Update retransmission statistics
                                    self.retransmission_counts[seq_num] += 1
                
                # Sleep to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error handling retransmissions: {e}")
    
    def calculate_final_statistics(self):
        """
        Calculate and log final statistics.
        """
        logger.info("=== Final Statistics ===")
        logger.info(f"Total packets sent: {self.total_sent}")
        logger.info(f"Total packets dropped: {self.total_dropped}")
        logger.info(f"Total packets retransmitted: {self.total_retransmitted}")
        logger.info(f"Total packets acknowledged: {len(self.acked_packets)}")
        
        # Calculate retransmission statistics
        retransmission_table = {}
        for count in range(1, 5):  # 1 to 4 retransmissions
            packets_with_count = sum(1 for seq_num, retrans_count in self.retransmission_counts.items() 
                                    if retrans_count == count)
            retransmission_table[count] = packets_with_count
            logger.info(f"Packets with {count} retransmissions: {packets_with_count}")
    
    def get_statistics(self):
        """
        Get client statistics for visualization and reporting.
        
        Returns:
            dict: Dictionary containing client statistics
        """
        with self.lock:
            stats = {
                'client_address': f"{socket.gethostbyname(socket.gethostname())}",
                'server_address': f"{self.server_host}:{self.server_port}",
                'total_sent': self.total_sent,
                'total_dropped': self.total_dropped,
                'total_retransmitted': self.total_retransmitted,
                'total_acked': len(self.acked_packets),
                'window_sizes': self.window_sizes,
                'window_timestamps': self.window_timestamps,
                'retransmission_counts': dict(self.retransmission_counts)
            }
        
        return stats

def main():
    """
    Main function to start the TCP client.
    """
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
    
    client.start()

if __name__ == "__main__":
    main()
