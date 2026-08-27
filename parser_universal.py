
import pandas as pd
import xml.etree.ElementTree as ET
from Evtx.Evtx import Evtx
from datetime import datetime
import re

def parse_evtx_to_df(file_path, max_events=None):
    """
    UNIVERSAL EVTX PARSER - Works with ANY event log type.
    Extracts EVERYTHING it can find, then intelligently maps fields.
    
    Parameters:
        file_path: Path to .evtx file
        max_events: Limit for testing (None = all events)
    
    Returns:
        DataFrame with standardized columns
    """
    
    # Namespace handling - EVTX always uses this
    NS = {'e': 'http://schemas.microsoft.com/win/2004/08/events/event'}
    
    all_records = []
    
    with Evtx(file_path) as log:
        event_count = 0
        for record in log.records():
            if max_events and event_count >= max_events:
                break
                
            try:
                xml_str = record.xml()
                root = ET.fromstring(xml_str)
                
                # --- Step 1: Extract System fields (always present) ---
                system = root.find('.//e:System', NS)
                system_data = {}
                if system is not None:
                    for elem in system:
                        # Handle child elements with text
                        if elem.text and elem.text.strip():
                            # Remove namespace prefix for clean keys
                            tag = elem.tag.split('}')[-1]
                            system_data[tag] = elem.text.strip()
                        # Handle attributes (like TimeCreated)
                        for attr, value in elem.attrib.items():
                            if value:
                                key = f"{elem.tag.split('}')[-1]}_{attr}"
                                system_data[key] = value
                
                # --- Step 2: Extract ALL EventData fields ---
                event_data = {}
                event_data_elem = root.find('.//e:EventData', NS)
                if event_data_elem is not None:
                    for data in event_data_elem.findall('.//e:Data', NS):
                        name = data.get('Name')
                        if name and data.text:
                            # Field has a Name attribute (Security logs)
                            event_data[name] = data.text.strip()
                        elif data.text:
                            # Field has NO Name attribute (some logs)
                            # Use position index
                            idx = len(event_data)
                            event_data[f'Data_{idx}'] = data.text.strip()
                
                # --- Step 3: Extract ALL data from .//Data (fallback) ---
                # Some logs put Data directly under Event
                for data in root.findall('.//Data'):
                    if data.get('Name') and data.text:
                        if data.get('Name') not in event_data:
                            event_data[data.get('Name')] = data.text.strip()
                
                # --- Step 4: Build the complete record ---
                record_data = {
                    # System fields
                    'event_id': system_data.get('EventID'),
                    'version': system_data.get('Version'),
                    'level': system_data.get('Level'),
                    'task': system_data.get('Task'),
                    'opcode': system_data.get('Opcode'),
                    'keywords': system_data.get('Keywords'),
                    'timestamp': system_data.get('TimeCreated_SystemTime'),
                    'event_record_id': system_data.get('EventRecordID'),
                    'provider_name': system_data.get('Provider_Name'),
                    'computer': system_data.get('Computer'),
                    'channel': system_data.get('Channel'),
                    'process_id': system_data.get('Execution_ProcessID'),
                    'thread_id': system_data.get('Execution_ThreadID'),
                }
                
                # Merge EventData fields
                record_data.update(event_data)
                
                # Also store the raw data for debugging
                record_data['_raw_data'] = str(event_data)[:500]
                
                all_records.append(record_data)
                event_count += 1
                
            except Exception as e:
                # Skip malformed entries
                continue
    
    # --- Step 5: Convert to DataFrame ---
    df = pd.DataFrame(all_records)
    
    # --- Step 6: Standardize timestamps ---
    if 'timestamp' in df.columns and len(df) > 0:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
        except:
            print("⚠️ Timestamp conversion had issues - check format")
    
    # --- Step 7: Add descriptive summary ---
    print(f"✅ Parsed {len(df)} events from {file_path}")
    if len(df) > 0:
        print(f"   📊 Event IDs found: {sorted(df['event_id'].dropna().unique())[:20]}")
        print(f"   📊 Columns extracted: {len(df.columns)}")
        
        # Show which Event IDs we have
        event_counts = df['event_id'].value_counts().head(5)
        print("   📊 Top events:")
        for eid, count in event_counts.items():
            print(f"      - {eid}: {count} events")
    
    return df

def map_to_common_fields(df):
    """
    Maps extracted data to common field names across different log types.
    This makes it easier to work with data from different sources.
    """
    # Define common field mappings
    mappings = {
        'username': ['TargetUserName', 'SubjectUserName', 'AccountName', 'UserName', 'User'],
        'command_line': ['CommandLine', 'NewProcessName', 'Image', 'ProcessName'],
        'process_id': ['ProcessId', 'NewProcessId', 'ProcessID'],
        'source_ip': ['IpAddress', 'SourceAddress', 'ClientAddress', 'IPAddress'],
        'source_port': ['IpPort', 'SourcePort'],
        'target': ['WorkstationName', 'ComputerName', 'TargetHostName'],
        'logon_type': ['LogonType'],
        'status': ['Status', 'FailureReason'],
        'session_id': ['LogonId', 'TargetLogonId', 'SubjectLogonId'],
    }
    
    # Create standardized columns
    for std_name, possible_fields in mappings.items():
        for field in possible_fields:
            if field in df.columns:
                df[std_name] = df[field]
                break
    
    return df

if __name__ == "__main__":
    print("Universal EVTX parser loaded.")
    print("This parser works with ANY EVTX file, regardless of log type.")
