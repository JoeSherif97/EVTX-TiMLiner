"""
Visualize EVTX attack chain as a graph
Usage: python visualize_chain.py <path_to_evtx_file>
"""

import sys
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from parser_universal import parse_evtx_to_df, map_to_common_fields

def create_attack_graph(df, input_file, output_file=None):
    """Create a visual attack chain graph"""
    
    if len(df) < 2:
        print("⚠️ Not enough events for visualization (need at least 2)")
        return None
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes for each event
    for idx, row in df.iterrows():
        event_id = row.get('event_id', 'Unknown')
        time_str = row.get('timestamp', 'Unknown')
        if pd.notna(time_str) and time_str != 'Unknown':
            time_str = time_str.strftime('%H:%M:%S')
        else:
            time_str = 'Unknown'
        
        # Create descriptive label
        if str(event_id) == '4625':
            label = f"❌ Failed\n{time_str}"
        elif str(event_id) == '4624':
            label = f"✅ Success\n{time_str}"
        elif str(event_id) == '3':
            dest_ip = row.get('DestinationIp', 'N/A')
            label = f"🌐 Network\n{time_str}\n→{dest_ip}"
        elif str(event_id) == '10':
            target = row.get('TargetImage', '')
            if 'lsass' in str(target).lower():
                label = f"🔐 Credential\n{time_str}\nMimikatz!"
            else:
                label = f"🔐 Process\n{time_str}"
        elif str(event_id) == '4688':
            cmd = row.get('command_line', '')
            label = f"💻 Process\n{time_str}\n{str(cmd)[:20]}"
        else:
            label = f"Event {event_id}\n{time_str}"
        
        G.add_node(idx, label=label, event=event_id)
    
    # Connect events chronologically
    for idx in range(len(df) - 1):
        G.add_edge(idx, idx+1, weight=1)
    
    # Draw
    plt.figure(figsize=(14, 6))
    pos = nx.spring_layout(G, k=3, seed=42)
    
    # Color by event type
    color_map = {
        '4624': '#2ECC71',  # Green - success
        '4625': '#E74C3C',  # Red - failure
        '3': '#3498DB',     # Blue - network
        '10': '#E67E22',    # Orange - process access
        '4688': '#9B59B6',  # Purple - process creation
    }
    colors = [color_map.get(str(G.nodes[n]['event']), '#95A5A6') for n in G.nodes()]
    
    nx.draw(G, pos, 
            node_color=colors,
            node_size=3500,
            with_labels=True,
            labels=nx.get_node_attributes(G, 'label'),
            font_size=8,
            font_weight='bold',
            arrows=True,
            arrowsize=20,
            edge_color='gray',
            edge_width=2)
    
    plt.title(f"Attack Chain Analysis: {os.path.basename(input_file)}", fontsize=14)
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✅ Graph saved: {output_file}")
    
    plt.show()
    return G

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize EVTX attack chain')
    parser.add_argument('file_path', help='Path to .evtx file')
    parser.add_argument('--output', '-o', help='Output PNG file path')
    
    args = parser.parse_args()
    
    input_file = args.file_path
    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    # Parse the file
    print(f"🔍 Analyzing: {input_file}")
    df = parse_evtx_to_df(input_file)
    
    if len(df) == 0:
        print("❌ No events parsed from file")
        sys.exit(1)
    
    # Map fields
    df_mapped = map_to_common_fields(df)
    
    # Set output file
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = os.path.dirname(input_file) or '.'
        output_file = os.path.join(output_dir, f"{base_name}_chain.png")
    
    # Create graph
    create_attack_graph(df_mapped, input_file, output_file)

if __name__ == "__main__":
    main()
