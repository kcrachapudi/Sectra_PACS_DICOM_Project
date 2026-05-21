import sys
from pynetdicom import AE
from pydicom import dcmread

def push_file(file_path, server_ip="127.0.0.1", server_port=11112):
    print("=" * 60)
    print(" Initializing Modality Client (C-STORE SCU)")
    print("=" * 60)
    
    # Read the file we want to push from disk
    try:
        ds = dcmread(file_path)
    except Exception as e:
        print(f"[!] Fail: Could not read file at {file_path}. Error: {e}")
        return

    # Define our local client application profile identity
    ae = AE(ae_title="SCANNER_ROOM_1")
    
    # Request a presentation context that matches the specific SOP Class of our target file
    ae.add_requested_context(ds.SOPClassUID)
    
    print(f"[1] Attempting network association handshake...")
    print(f"    Calling AE: SCANNER_ROOM_1  --->  Called AE: SECTRA_MINI_PACS")
    
    # Establish association with our server node
    assoc = ae.associate(server_ip, server_port, ae_title="SECTRA_MINI_PACS")
    
    if assoc.is_established:
        print("[2] Association Accepted! Handshake Cleared. Secure port open.")
        print(f"[3] Executing C-STORE pipeline for file...")
        
        # Stream the file across the wire
        status = assoc.send_c_store(ds)
        
        # Check if the server returned our 0x0000 success signal
        if status and status.Status == 0x0000:
            print("[✔] Transaction Verified: File successfully stored in remote archive.")
        else:
            print(f"[!] Error: Server rejected storage request. Status: {status}")
        
        # Always tear down the connection when finished
        print("[4] Releasing network association thread...")
        assoc.release()
    else:
        print("[!] Handshake Failed: Connection rejected by PACS server.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    # Point this to the original or your modified file path
    target_file = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Dicom-Test-Files/MR_small_anonymized.dcm"
    push_file(target_file)