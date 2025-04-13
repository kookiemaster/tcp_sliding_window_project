#!/usr/bin/env python3
"""
TCP Sliding Window Protocol - Visualization Module
CS 258 Project Assignment

Author: Xiangyi Li (xiangyi@benchflow.ai)

This visualization module:
1. Creates graphs for TCP window sizes over time
2. Creates graphs for sequence numbers received/dropped over time
3. Creates a table for retransmission statistics
4. Generates a comprehensive report with all visualizations
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator
from datetime import datetime

class TCPVisualizer:
    """
    Visualization class for TCP sliding window protocol statistics.
    """
    
    def __init__(self, output_dir='./output'):
        """
        Initialize the TCP visualizer.
        
        Args:
            output_dir (str): Directory to save visualization outputs
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Set plot style
        plt.style.use('ggplot')
        
        # Timestamp for file naming
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def load_data(self, client_stats_file, server_stats_file):
        """
        Load statistics data from client and server.
        
        Args:
            client_stats_file (str): Path to client statistics JSON file
            server_stats_file (str): Path to server statistics JSON file
            
        Returns:
            tuple: (client_stats, server_stats) dictionaries
        """
        # Load client statistics
        with open(client_stats_file, 'r') as f:
            client_stats = json.load(f)
        
        # Load server statistics
        with open(server_stats_file, 'r') as f:
            server_stats = json.load(f)
        
        return client_stats, server_stats
    
    def plot_window_sizes(self, client_stats, server_stats):
        """
        Plot TCP sender and receiver window sizes over time.
        
        Args:
            client_stats (dict): Client statistics
            server_stats (dict): Server statistics
            
        Returns:
            str: Path to saved plot
        """
        plt.figure(figsize=(12, 6))
        
        # Plot client window size
        plt.plot(
            client_stats['window_timestamps'], 
            client_stats['window_sizes'],
            label='Sender Window Size',
            alpha=0.7
        )
        
        # Set plot properties
        plt.title('TCP Sender and Receiver Window Size Over Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Window Size')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        output_path = os.path.join(self.output_dir, f'window_sizes_{self.timestamp}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_sequence_numbers(self, server_stats):
        """
        Plot TCP sequence numbers received over time.
        
        Args:
            server_stats (dict): Server statistics
            
        Returns:
            str: Path to saved plot
        """
        plt.figure(figsize=(12, 6))
        
        # Get sequence numbers and timestamps
        seq_nums = server_stats['seq_nums_received']
        timestamps = server_stats['seq_timestamps']
        
        # Create a scatter plot with small points
        plt.scatter(
            timestamps, 
            seq_nums,
            s=1,  # Small point size
            alpha=0.5,
            label='Received Sequence Numbers'
        )
        
        # Set plot properties
        plt.title('TCP Sequence Numbers Received Over Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Sequence Number')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        output_path = os.path.join(self.output_dir, f'seq_nums_received_{self.timestamp}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_dropped_packets(self, server_stats):
        """
        Plot TCP sequence numbers dropped over time.
        
        Args:
            server_stats (dict): Server statistics
            
        Returns:
            str: Path to saved plot
        """
        plt.figure(figsize=(12, 6))
        
        # Get dropped sequence numbers
        dropped_seq_nums = server_stats['seq_nums_dropped']
        
        # Create histogram of dropped packets
        plt.hist(
            dropped_seq_nums, 
            bins=50,
            alpha=0.7,
            color='red',
            label='Dropped Sequence Numbers'
        )
        
        # Set plot properties
        plt.title('TCP Sequence Numbers Dropped')
        plt.xlabel('Sequence Number')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        output_path = os.path.join(self.output_dir, f'seq_nums_dropped_{self.timestamp}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_retransmission_table(self, client_stats):
        """
        Create a table of retransmission statistics.
        
        Args:
            client_stats (dict): Client statistics
            
        Returns:
            tuple: (DataFrame, path to saved CSV)
        """
        # Count retransmissions
        retrans_counts = client_stats['retransmission_counts']
        
        # Create a dictionary to store counts for each retransmission number
        retrans_table = {
            '# of retransmissions': [],
            '# of packets': []
        }
        
        # Count packets with 1, 2, 3, and 4 retransmissions
        for retrans_num in range(1, 5):
            count = sum(1 for _, count in retrans_counts.items() if count == retrans_num)
            retrans_table['# of retransmissions'].append(retrans_num)
            retrans_table['# of packets'].append(count)
        
        # Create DataFrame
        df = pd.DataFrame(retrans_table)
        
        # Save to CSV
        output_path = os.path.join(self.output_dir, f'retransmission_table_{self.timestamp}.csv')
        df.to_csv(output_path, index=False)
        
        return df, output_path
    
    def plot_goodput(self, server_stats):
        """
        Plot goodput measurements over time.
        
        Args:
            server_stats (dict): Server statistics
            
        Returns:
            str: Path to saved plot
        """
        plt.figure(figsize=(12, 6))
        
        # Get goodput measurements and timestamps
        goodput = server_stats['goodput_measurements']
        timestamps = server_stats['measurement_timestamps']
        
        # Plot goodput
        plt.plot(
            timestamps, 
            goodput,
            label='Goodput',
            color='green',
            marker='o',
            markersize=3,
            linestyle='-',
            linewidth=1
        )
        
        # Calculate and plot average goodput
        avg_goodput = np.mean(goodput)
        plt.axhline(
            y=avg_goodput, 
            color='blue', 
            linestyle='--',
            label=f'Average Goodput: {avg_goodput:.4f}'
        )
        
        # Set plot properties
        plt.title('Goodput Over Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Goodput (received/sent)')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        output_path = os.path.join(self.output_dir, f'goodput_{self.timestamp}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, client_stats, server_stats):
        """
        Generate a comprehensive report with all visualizations.
        
        Args:
            client_stats (dict): Client statistics
            server_stats (dict): Server statistics
            
        Returns:
            dict: Paths to all generated files
        """
        # Generate all visualizations
        window_plot_path = self.plot_window_sizes(client_stats, server_stats)
        seq_nums_plot_path = self.plot_sequence_numbers(server_stats)
        dropped_plot_path = self.plot_dropped_packets(server_stats)
        goodput_plot_path = self.plot_goodput(server_stats)
        retrans_df, retrans_table_path = self.create_retransmission_table(client_stats)
        
        # Create summary statistics
        summary = {
            'client_address': client_stats['client_address'],
            'server_address': server_stats['server_address'],
            'total_packets_sent': client_stats['total_sent'],
            'total_packets_received': server_stats['total_packets_received'],
            'total_packets_dropped': client_stats['total_dropped'],
            'total_packets_retransmitted': client_stats['total_retransmitted'],
            'average_goodput': np.mean(server_stats['goodput_measurements']),
            'retransmission_table': retrans_df.to_dict(),
            'visualization_paths': {
                'window_sizes': window_plot_path,
                'sequence_numbers_received': seq_nums_plot_path,
                'sequence_numbers_dropped': dropped_plot_path,
                'goodput': goodput_plot_path,
                'retransmission_table': retrans_table_path
            }
        }
        
        # Save summary to JSON
        summary_path = os.path.join(self.output_dir, f'summary_{self.timestamp}.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=4)
        
        return summary

def main():
    """
    Main function to run the TCP visualizer.
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TCP Sliding Window Protocol Visualizer')
    parser.add_argument('--client', required=True, help='Path to client statistics JSON file')
    parser.add_argument('--server', required=True, help='Path to server statistics JSON file')
    parser.add_argument('--output', default='./output', help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = TCPVisualizer(output_dir=args.output)
    
    # Load data
    client_stats, server_stats = visualizer.load_data(args.client, args.server)
    
    # Generate report
    summary = visualizer.generate_report(client_stats, server_stats)
    
    print(f"Report generated successfully. Summary saved to {args.output}/summary_*.json")
    print(f"Visualizations saved to {args.output}/")

if __name__ == "__main__":
    main()
