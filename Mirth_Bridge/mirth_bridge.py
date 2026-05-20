import os
import socket
import json

# Force absolute pathing to the root project folder
BASE_DIR = "/home/augustus/Projects/Sectra_Project"
WORKLIST_DIR = "/home/augustus/Projects/Sectra_Project/Scanner_Worklist"

# MLLP Protocol Wrappers
VT, FS, CR = b'\x0b', b'\x1c', b'\x0d'

def parse_hl7_segment(msg_lines, segment_id):
    """Finds a specific segment (e.g., 'PID') and splits it by pipe characters."""
    for line in msg_lines:
        if line.startswith(segment_id):
            return line.split('|')
    return None

def start_bridge():
    # Ensure the worklist directory exists
    os.makedirs(WORKLIST_DIR, exist_ok=True)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 4444))
        s.listen(1)
        print("\n" + "="*60)
        print("[CUSTOM MIRTH BRIDGE] Middleware active on port 4444...")
        print("Waiting to ingest, digest, and route clinical data...")
        print("="*60 + "\n")
        
        message_id = 1000
        
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if not data:
                    continue
                
                # 1. Strip MLLP framing to "ingest" the raw text
                raw_hl7 = data.replace(VT, b'').replace(FS, b'').decode('utf-8')
                lines = raw_hl7.split('\r')
                
                print("[Bridge] Ingested raw HL7 message payload. Beginning digestion...")
                
                # 2. Extract specific segments ("Digestion")
                pid_seg = parse_hl7_segment(lines, "PID")
                orc_seg = parse_hl7_segment(lines, "ORC")
                obr_seg = parse_hl7_segment(lines, "OBR")
                
                if pid_seg and orc_seg and obr_seg:
                    # Map fields by their HL7 array index positions
                    patient_id = pid_seg[3].split('^')[0]
                    
                    # Handle name parsing (Last^First)
                    name_parts = pid_seg[5].split('^')
                    patient_name = f"{name_parts[0]}, {name_parts[1]}" if len(name_parts) > 1 else name_parts[0]
                    
                    accession_number = orc_seg[2]
                    procedure = obr_seg[4].split('^')[1] if '^' in obr_seg[4] else obr_seg[4]
                    
                    # 3. Restructure into the target schema ("Distribution")
                    worklist_data = {
                        "patient_id": patient_id,
                        "patient_name": patient_name,
                        "accession_number": accession_number,
                        "procedure": procedure
                    }
                    
                    # Write the JSON payload directly into the Imager's folder
                    file_path = os.path.join(WORKLIST_DIR, f"order_{message_id}.json")
                    with open(file_path, 'w') as f:
                        json.dump(worklist_data, f, indent=4)
                    
                    print(f"[Bridge] Successfully digested message. Dropped worklist token to: {file_path}")
                    message_id += 1
                    
                    # Send standard MLLP ACK (Acknowledgment) back to EMR to close the network transaction
                    ack_msg = f"MSH|^~\\&|MIRTH_BRIDGE|SYSTEM|EPIC|HOSPITAL|202605191200||MSA^O01|MSGACK||P|2.3|\rMSA|AA|MSG00002|"
                    conn.sendall(VT + ack_msg.encode('utf-8') + FS + CR)
                else:
                    print("[Bridge] Error: Outbound payload missing required HL7 segments.")

if __name__ == "__main__":
    start_bridge()