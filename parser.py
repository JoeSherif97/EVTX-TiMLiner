# Cell 3: Write our Parser Python file directly into the GitHub repo
%%writefile /content/evtx-ml-timeline/parser.py

import pandas as pd
import xml.etree.ElementTree as ET
from Evtx.Evtx import Evtx
from Evtx.Views import evtx_file_xml_view
import re

def parse_evtx_to_df(file_path):
    """
    Reads a .evtx file and extracts: Time, EventID, User, CommandLine, ProcessID
    """
    records = []
    
    with Evtx(file_path) as log:
        for record in log.records():
            try:
                xml_str = record.xml()
                root = ET.fromstring(xml_str)
                
                # Extract Timestamp
                time_node = root.find(".//TimeCreated")
                timestamp = time_node.get('SystemTime') if time_node is not None else None
                
                # Extract Event ID
                event_id_node = root.find(".//EventID")
                event_id = event_id_node.text if event_id_node is not None else None
                
                # Extract User (from Security logs)
                user_node = root.find(".//Data[@Name='TargetUserName']")
                user = user_node.text if user_node is not None else "SYSTEM"
                
                # Extract Command Line (from Process creation logs - Event 4688)
                cmd_node = root.find(".//Data[@Name='CommandLine']")
                command_line = cmd_node.text if cmd_node is not None else ""
                
                # Extract Process ID
                pid_node = root.find(".//Data[@Name='ProcessId']")
                pid = pid_node.text if pid_node is not None else None
                
                records.append({
                    'timestamp': timestamp,
                    'event_id': event_id,
                    'user': user,
                    'command_line': command_line,
                    'process_id': pid
                })
            except:
                # Skip malformed XML entries
                continue
                
    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"✅ Parsed {len(df)} events from {file_path}")
    return df

if __name__ == "__main__":
    # Test function when run directly
    print("Parser module loaded successfully.")
