import os
import traceback
from pynetdicom import AE, evt, AllStoragePresentationContexts
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelMove
)
from pydicom import dcmread, Dataset

STORAGE_DIR = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Pacs_Vault"
PACS_AE_TITLE = "SECTRA_MINI_PACS"
LISTEN_PORT = 11112

def handle_store(event):
    ds = event.dataset
    ds.file_meta = event.file_meta
    patient_id = ds.get("PatientID", "UNKNOWN_ID")
    study_uid = ds.get("StudyInstanceUID", "UNKNOWN_STUDY")
    sop_uid = ds.get("SOPInstanceUID", "UNKNOWN_INSTANCE")
    
    study_folder = os.path.join(STORAGE_DIR, str(patient_id), str(study_uid))
    os.makedirs(study_folder, exist_ok=True)
    output_filename = os.path.join(study_folder, f"{sop_uid}.dcm")
    ds.save_as(output_filename, write_like_original=False)
    return 0x0000

def handle_find(event):
    search_criteria = event.identifier
    target_id = search_criteria.get("PatientID", None)
    
    for root, dirs, files in os.walk(STORAGE_DIR):
        for file in files:
            if file.endswith(".dcm"):
                ds = dcmread(os.path.join(root, file), stop_before_pixels=True)
                if target_id is None or ds.PatientID == target_id:
                    response_ds = Dataset()
                    response_ds.PatientName = ds.PatientName
                    response_ds.PatientID = ds.PatientID
                    response_ds.StudyInstanceUID = ds.StudyInstanceUID
                    response_ds.QueryRetrieveLevel = search_criteria.QueryRetrieveLevel
                    yield 0xFF00, response_ds
    yield 0x0000, None

def handle_move(event):
    """
    Out-of-Band C-MOVE Handler.
    Dynamically builds requested presentation contexts based strictly on files found.
    """
    print("\n" + "="*50)
    print("[*] Inbound Direct-Pump C-MOVE Activated!")
    
    try:
        move_criteria = event.identifier
        target_study_uid = move_criteria.get("StudyInstanceUID", None)
        destination_ae = event.move_destination
        
        print(f"[+] Requesting Study UID: {target_study_uid}")
        print(f"[+] Target Destination AE Title: {destination_ae}")
        print("="*50)

        ae_routing_table = {
            "CLINIC_WORKSTN": ("127.0.0.1", 11115)
        }
        
        if destination_ae not in ae_routing_table:
            print(f"[!] Unknown Destination AE: {destination_ae}")
            return 0xA801  # Move Destination Unknown

        dest_ip, dest_port = ae_routing_table[destination_ae]
        
        # Gather matching files and collect unique SOP Classes
        matching_files = []
        required_sop_classes = set()
        
        for root, dirs, files in os.walk(STORAGE_DIR):
            for file in files:
                if file.endswith(".dcm"):
                    file_path = os.path.join(root, file)
                    ds = dcmread(file_path)
                    if ds.StudyInstanceUID == target_study_uid:
                        matching_files.append(ds)
                        # Read SOP Class UID from file metadata or dataset
                        sop_class = ds.file_meta.MediaStorageSOPClassUID if 'file_meta' in ds else ds.SOPClassUID
                        required_sop_classes.add(str(sop_class))

        num_files = len(matching_files)
        print(f"[+] Direct Pump Engine: Found {num_files} files to push.")
        
        if num_files > 0:
            pump_ae = AE(ae_title=PACS_AE_TITLE)
            
            # Dynamically request ONLY the exact storage contexts needed for this payload
            for sop_class in required_sop_classes:
                pump_ae.add_requested_context(sop_class)
                print(f"[+] Added context presentation contract for SOP Class: {sop_class}")
            
            print(f"[->] Establishing dedicated transfer link to {dest_ip}:{dest_port}...")
            assoc = pump_ae.associate(dest_ip, dest_port, ae_title=destination_ae)
            
            if assoc.is_established:
                for idx, ds in enumerate(matching_files, 1):
                    print(f"[->] Pumping file {idx}/{num_files} directly via C-STORE...")
                    status = assoc.send_c_store(ds)
                    print(f"    -> Response status: 0x{status.Status:04x}")
                assoc.release()
                print("[✔] Direct-pump file streaming completed.")
            else:
                print("[!] Critical Error: Could not connect to client workstation listener!")
                return 0xA702  # Out of resources

        return 0x0000  # Clean Success status code

    except Exception as e:
        print("[!!!] Internal exception caught during C-MOVE execution:")
        traceback.print_exc()
        return 0xC000  # Unable to process

def start_server():
    ae = AE(ae_title=PACS_AE_TITLE)
    # Servers are completely allowed to support All Contexts (>128)
    ae.supported_contexts = AllStoragePresentationContexts
    ae.add_supported_context(PatientRootQueryRetrieveInformationModelFind)
    ae.add_supported_context(PatientRootQueryRetrieveInformationModelMove)
    
    handlers = [
        (evt.EVT_C_STORE, handle_store),
        (evt.EVT_C_FIND, handle_find),
        (evt.EVT_C_MOVE, handle_move)
    ]
    
    print("=" * 60)
    print(f" PACS LISTENER ACTIVE: C-STORE, C-FIND, & DYNAMIC SCU PUMP C-MOVE")
    print(f" AE Title: {PACS_AE_TITLE} | Port: {LISTEN_PORT}")
    print("=" * 60)
    
    ae.start_server(("", LISTEN_PORT), block=True, evt_handlers=handlers)

if __name__ == "__main__":
    start_server()