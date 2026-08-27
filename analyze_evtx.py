"""
EVTX Timeline Analyzer - Main Pipeline
Usage: python analyze_evtx.py <path_to_evtx_file>
Example: python analyze_evtx.py samples/sysmon_3_10_Invoke-Mimikatz_hosted_Github.evtx
"""

import sys
import os
import pandas as pd
import json
from datetime import datetime
import argparse

# Import our universal parser
from parser_universal import parse_evtx_to_df, map_to_common_fields

def generate_timeline_report(df, input_file):
    """Generate human-readable timeline report"""
    
    report_lines = []
    report_lines.append("="*80)
    report_lines.append("🔍 EVTX TIMELINE ANALYSIS REPORT")
    report_lines.append("="*80)
    report_lines.append(f"📁 File: {os.path.basename(input_file)}")
    report_lines.append(f"📊 Total Events: {len(df)}")
    
    if 'timestamp' in df.columns and not df['timestamp'].isna().all():
        report_lines.append(f"📅 Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    report_lines.append("")
    
    # Event breakdown
    report_lines.append("📊 EVENT BREAKDOWN:")
    if 'event_id' in df.columns:
        for eid, count in df['event_id'].value_counts().items():
            event_names = {
                '4624': 'Successful Logon',
                '4625': 'Failed Logon', 
                '4688': 'Process Creation',
                '3': 'Network Connection (Sysmon)',
                '10': 'Process Access (Sysmon)',
                '1': 'Process Creation (Sysmon)',
                '4104': 'PowerShell Script Block'
            }
            name = event_names.get(str(eid), f'Event {eid}')
            report_lines.append(f"  - {eid}: {count} ({name})")
    report_lines.append("")
    
    # Build the attack chain story
    report_lines.append("🔗 ATTACK CHAIN STORY:")
    report_lines.append("")
    
    attack_detected = False
    attack_type = "Unknown"
    
    for idx, row in df.iterrows():
        event_id = row.get('event_id')
        time_str = row.get('timestamp', 'Unknown')
        if pd.notna(time_str) and time_str != 'Unknown':
            time_str = time_str.strftime('%H:%M:%S.%f')[:-3]
        
        # Get standardized fields
        user = row.get('username', row.get('TargetUserName', row.get('SubjectUserName', 'N/A')))
        source_ip = row.get('source_ip', row.get('IpAddress', 'N/A'))
        target = row.get('target', row.get('WorkstationName', row.get('Computer', 'N/A')))
        
        # Describe event types
        if str(event_id) == '4625':
            report_lines.append(f"  Step {idx+1}: ❌ FAILED LOGON ({time_str})")
            report_lines.append(f"     → User: {user} on {target}")
            report_lines.append(f"     → Source IP: {source_ip}")
            attack_type = "Brute Force Attack"
            attack_detected = True
            
        elif str(event_id) == '4624':
            report_lines.append(f"  Step {idx+1}: ✅ SUCCESSFUL LOGON ({time_str})")
            report_lines.append(f"     → User: {user} on {target}")
            report_lines.append(f"     → Logon Type: {row.get('logon_type', 'N/A')}")
            if attack_type == "Brute Force Attack":
                report_lines.append(f"     → 🚨 Success after previous failures - Attack successful!")
            
        elif str(event_id) == '3':  # Sysmon Network
            report_lines.append(f"  Step {idx+1}: 🌐 NETWORK CONNECTION ({time_str})")
            report_lines.append(f"     → Destination: {row.get('DestinationIp', 'N/A')}:{row.get('DestinationPort', 'N/A')}")
            report_lines.append(f"     → Process: PID {row.get('process_id', 'N/A')}")
            if 'github' in str(row.get('DestinationIp', '')).lower():
                report_lines.append(f"     → ⚠️  GitHub download detected - possible payload download!")
                attack_type = "Malware Download"
                attack_detected = True
                
        elif str(event_id) == '10':  # Sysmon Process Access
            target_image = row.get('TargetImage', '')
            report_lines.append(f"  Step {idx+1}: 🔐 PROCESS ACCESS ({time_str})")
            report_lines.append(f"     → Source PID: {row.get('SourceProcessId', 'N/A')}")
            report_lines.append(f"     → Target PID: {row.get('TargetProcessId', 'N/A')}")
            report_lines.append(f"     → Target: {target_image}")
            if 'lsass' in str(target_image).lower():
                report_lines.append(f"     → 🚨 LSASS.EXE ACCESS - CREDENTIAL DUMPING DETECTED!")
                attack_type = "Credential Dumping (Mimikatz)"
                attack_detected = True
                
        elif str(event_id) == '4688':
            cmd = row.get('command_line', row.get('CommandLine', ''))
            report_lines.append(f"  Step {idx+1}: 💻 PROCESS CREATED ({time_str})")
            report_lines.append(f"     → Command: {cmd[:80]}{'...' if len(str(cmd)) > 80 else ''}")
            
        else:
            report_lines.append(f"  Step {idx+1}: 📋 Event {event_id} ({time_str})")
            report_lines.append(f"     → User: {user}")
    
    # Add alert summary
    report_lines.append("")
    report_lines.append("="*80)
    if attack_detected:
        report_lines.append(f"🔴 ALERT: {attack_type} DETECTED")
        report_lines.append("")
        report_lines.append("📌 Indicators of Compromise (IOCs):")
        
        # Extract IOCs from the data
        if 'source_ip' in df.columns:
            ips = df['source_ip'].dropna().unique()
            if len(ips) > 0 and ips[0] not in ['-', '127.0.0.1', '::1']:
                report_lines.append(f"   - Source IP: {', '.join(ips[:5])}")
        
        if 'DestinationIp' in df.columns:
            dest_ips = df['DestinationIp'].dropna().unique()
            if len(dest_ips) > 0:
                report_lines.append(f"   - Destination IPs: {', '.join(dest_ips[:5])")
        
        report_lines.append("   - Suspicious process behavior pattern")
        report_lines.append("")
        report_lines.append("🎯 Recommended Response:")
        report_lines.append("   - Isolate affected host immediately")
        report_lines.append("   - Review event logs for lateral movement")
        report_lines.append("   - Reset compromised credentials")
        report_lines.append("   - Conduct full system scan")
    else:
        report_lines.append("✅ No known attack patterns detected")
        report_lines.append("   (Regular monitoring continues)")
    
    report_lines.append("="*80)
    
    return "\n".join(report_lines)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze EVTX file and generate timeline')
    parser.add_argument('file_path', help='Path to .evtx file')
    parser.add_argument('--output', '-o', help='Output directory (default: same as input)')
    parser.add_argument('--json', action='store_true', help='Also output JSON format')
    
    args = parser.parse_args()
    
    input_file = args.file_path
    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    # Set output directory
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.dirname(input_file) or '.'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse the file
    print(f"🔍 Analyzing: {input_file}")
    df = parse_evtx_to_df(input_file)
    
    if len(df) == 0:
        print("❌ No events parsed from file")
        sys.exit(1)
    
    # Map to common fields
    df_mapped = map_to_common_fields(df)
    
    # Generate report
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    report_text = generate_timeline_report(df_mapped, input_file)
    
    # Save text report
    report_file = os.path.join(output_dir, f"{base_name}_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"✅ Report saved: {report_file}")
    
    # Save JSON (if requested)
    if args.json:
        json_file = os.path.join(output_dir, f"{base_name}_data.json")
        # Convert DataFrame to JSON-safe format
        json_data = df_mapped.to_dict(orient='records')
        # Convert timestamps to strings
        for record in json_data:
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        print(f"✅ JSON data saved: {json_file}")
    
    # Print report to console
    print("\n" + report_text)
    
    # Return report for programmatic use
    return report_text

if __name__ == "__main__":
    main()
