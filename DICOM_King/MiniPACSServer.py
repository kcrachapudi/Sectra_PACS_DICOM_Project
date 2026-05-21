import os
from pynetdicom import AE, evt, AllStoragePresentationContexts  # UPDATED IMPORT
from pydicom import dcmread

# Define where the PACS will permanently store incoming binary objects
STORAGE_DIR = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Pacs_Vault"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Define our secure server identity coordinates
PACS_AE_TITLE = "SECTRA_MINI_PACS"
LISTEN_PORT = 11112  # Standard DICOM port is 104 or 11112

def handle_store(event):
    """Callback function executed every time a client pushes a file via C-STORE."""
    print("\n" + "-"*50)
    print("[*] Incoming C-STORE request detected!")
    
    # Extract the raw dataset from the network stream
    ds = event.dataset
    
    # Force the meta header information to parse
    ds.file_meta = event.file_meta
    
    # Extract structural identities for directory routing
    patient_id = ds.get("PatientID", "UNKNOWN_ID")
    study_uid = ds.get("StudyInstanceUID", "UNKNOWN_STUDY")
    sop_uid = ds.get("SOPInstanceUID", "UNKNOWN_INSTANCE")
    
    print(f"[+] Routing to Vault -> Patient: {ds.get('PatientName', 'N/A')} ({patient_id})")
    print(f"[+] Target Study UID : {study_uid}")
    print(f"[+] Target Instance UID: {sop_uid}")

    # Build a highly organized hierarchy path: /Pacs_Vault/PatientID/StudyUID/SOP_UID.dcm
    study_folder = os.path.join(STORAGE_DIR, str(patient_id), str(study_uid))
    os.makedirs(study_folder, exist_ok=True)
    
    output_filename = os.path.join(study_folder, f"{sop_uid}.dcm")
    
    # Save the file down to our redundant storage tier
    ds.save_as(output_filename, write_like_original=False)
    print(f"[✔] Success: Binary file written securely to disk:\n    -> {output_filename}")
    print("-"*50)
    
    # Return a successful DICOM status code (0x0000 means Success)
    return 0x0000

def start_server():
    # Initialize our Application Entity (AE) profile
    ae = AE(ae_title=PACS_AE_TITLE)
    
    # UPDATED: Support presentation contexts for all storage SOP Classes
    ae.supported_contexts = AllStoragePresentationContexts
    
    # Bind the incoming event trigger to our handler function
    handlers = [(evt.EVT_C_STORE, handle_store)]
    
    print("=" * 60)
    print(f" INITIALIZING PACS LISTENER NODE: {PACS_AE_TITLE}")
    print(f" Port: {LISTEN_PORT} | Status: LISTENING FOR HANDSHAKES...")
    print("=" * 60)
    
    # Fire up the listener loop (this runs continuously until broken)
    ae.start_server(("", LISTEN_PORT), block=True, evt_handlers=handlers)

if __name__ == "__main__":
    start_server()