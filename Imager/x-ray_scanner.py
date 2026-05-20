import os
import json
import time
import socket

# Force absolute pathing to match the bridge exactly
BASE_DIR = "/home/augustus/Projects/Sectra_Project"
WORKLIST_DIR = "/home/augustus/Projects/Sectra_Project/Scanner_Worklist"
PACS_DIR = "/home/augustus/Projects/Sectra_Project/Sectra_Storage"
VT, FS, CR = b'\x0b', b'\x1c', b'\x0d'

print(f"[X-Ray Scanner] Modality active. Monitoring worklist queue: {WORKLIST_DIR}")

while True:
    files = [f for f in os.listdir(WORKLIST_DIR) if f.endswith('.json')]
    
    if files:
        worklist_file = os.path.join(WORKLIST_DIR, files[0])
        try:
            with open(worklist_file, 'r') as f:
                order_data = json.load(f)
        except Exception:
            time.sleep(0.5)
            continue
            
        print("\n" + "="*50)
        print(f"[SCANNER WORKLIST MASTER QUEUE]")
        print(f"Patient:    {order_data['patient_name']}")
        print(f"MRN ID:     {order_data['patient_id']}")
        print(f"Procedure:  {order_data['procedure']}")
        print("="*50)
        
        input("Press [ENTER] to execute exposure and weld DICOM tags...")
        print("[X-Ray Scanner] Capturing raw pixel grid...")
        
        # Simulating raw spatial matrix data (the voxels/pixels)
        dummy_pixel_matrix = [16, 42, 110, 255, 255, 180, 90, 12, 0, 4]
        
        dicom_mockup = {
            "DICOM_HEADER": {
                "0010,0010_PatientName": order_data['patient_name'],
                "0010,0020_PatientID": order_data['patient_id'],
                "0008,0050_AccessionNumber": order_data['accession_number'],
                "0008,0060_Modality": "DX"
            },
            "RAW_PIXEL_DATA": dummy_pixel_matrix
        }
        
        pacs_filename = f"CR_STUDY_{order_data['accession_number']}.dcm.json"
        with open(os.path.join(PACS_DIR, pacs_filename), 'w') as pacs_file:
            json.dump(dicom_mockup, pacs_file, indent=2)
        print(f"[DICOM C-STORE] Archived complete image file to storage pool.")
        
        print("[Sectra PACS] Compiling Radiology Text Report & Streaming URL...")
        time.sleep(1)
        
        accession = order_data['accession_number']
        sectra_url = f"https://sectra.hospital.local/viewer?accession={accession}"
        
        hl7_oru = (
            "MSH|^~\\&|SECTRA|PACS|EPIC|HOSPITAL|202605191202||ORU^R01|MSG00003|P|2.3|\r"
            f"PID|||{order_data['patient_id']}^^^MRN||{order_data['patient_name']}||\r"
            f"OBX|1|TX|RAD-REPORT^Report||FINDINGS: Clean fracture along distal radius. Alignment required.||\r"
            f"OBX|2|RP|VIEW-URL^Sectra Link||{sectra_url}|||"
        )
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as hospital_conn:
                hospital_conn.connect(('127.0.0.1', 5555))
                hospital_conn.sendall(VT + hl7_oru.encode('utf-8') + FS + CR)
                print("[Sectra PACS] HL7 ORU result pushed to EMR. Loop closed.")
        except Exception as e:
            print(f"[Sectra PACS] Failed to dispatch report back to EMR: {e}")
            
        os.remove(worklist_file)
        
    time.sleep(1)