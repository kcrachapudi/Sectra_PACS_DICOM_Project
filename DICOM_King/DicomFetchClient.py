import os
import time
from pynetdicom import AE, evt, AllStoragePresentationContexts
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelMove
from pydicom import Dataset

STORAGE_DIR = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Pacs_Vault"
CLIENT_DOWNLOAD_DIR = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Client_Downloads"
os.makedirs(CLIENT_DOWNLOAD_DIR, exist_ok=True)

def handle_incoming_store(event):
    """Catches files pushed back from the PACS server."""
    ds = event.dataset
    ds.file_meta = event.file_meta
    sop_uid = ds.get("SOPInstanceUID", "unknown_instance")
    
    out_path = os.path.join(CLIENT_DOWNLOAD_DIR, f"fetched_{sop_uid}.dcm")
    ds.save_as(out_path, write_like_original=False)
    print(f"[✔] Catch Success! Inbound image written to: {os.path.basename(out_path)}")
    return 0x0000

def get_a_real_study_uid():
    for root, dirs, files in os.walk(STORAGE_DIR):
        if len(dirs) == 0 and len(files) > 0:
            return os.path.basename(root)
    return None

def execute_pacs_move():
    target_study_uid = get_a_real_study_uid()
    if not target_study_uid:
        print("[!] Error: Could not locate any valid patient data directories inside Pacs_Vault.")
        return

    print("=" * 60)
    print(" Initializing Multi-Channel C-MOVE Client Workstation")
    print(f" Target Study UID: {target_study_uid}")
    print("=" * 60)

    client_ae = AE(ae_title="CLINIC_WORKSTN")
    client_ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)
    client_ae.supported_contexts = AllStoragePresentationContexts
    
    handlers = [(evt.EVT_C_STORE, handle_incoming_store)]
    
    # Fire up the background listener on port 11115
    scp_listener = client_ae.start_server(("", 11115), block=False, evt_handlers=handlers)
    print("[1] Workstation background storage receiver active on port 11115.")
    time.sleep(0.5)

    move_payload = Dataset()
    move_payload.QueryRetrieveLevel = "STUDY"
    move_payload.StudyInstanceUID = target_study_uid

    print("[2] Dialing MiniPACS on primary association port 11112...")
    assoc = client_ae.associate("127.0.0.1", 11112, ae_title="SECTRA_MINI_PACS")
    
    if assoc.is_established:
        print(f"[3] Association cleared. Sending C-MOVE request payload...")
        
        responses = assoc.send_c_move(
            move_payload, 
            "CLINIC_WORKSTN", 
            query_model=PatientRootQueryRetrieveInformationModelMove
        )
        
        # Iterate over the responses coming back from our manual pump execution
        for (status, identifier) in responses:
            if status:
                if status.Status == 0x0000: 
                    print("[✔] Move transaction reported complete and successful by PACS.")
                else:
                    print(f"[i] Status Code: 0x{status.Status:04x}")
            
        assoc.release()
        print("[4] Primary transaction link released cleanly.")
    else:
        print("[!] Critical Error: Association rejected by MiniPACS server.")
        
    # Give the background disk writers an extra moment to flush to disk cleanly
    time.sleep(1.0)
    scp_listener.shutdown()
    print("[5] Target Workstation listener closed down. Process complete.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    execute_pacs_move()