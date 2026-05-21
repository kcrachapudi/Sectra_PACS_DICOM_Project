import os
from pynetdicom import AE
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind
from pydicom import Dataset

STORAGE_DIR = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Pacs_Vault"

def get_a_real_patient_id():
    """Scans the vault filesystem to find a real, active Patient ID automatically."""
    for root, dirs, files in os.walk(STORAGE_DIR):
        # The parent directories immediately inside Pacs_Vault are the Patient IDs
        if root != STORAGE_DIR:
            relative_path = os.path.relpath(root, STORAGE_DIR)
            path_parts = relative_path.split(os.sep)
            if path_parts[0]:
                return path_parts[0]
    return "PATIENT_ID_003" # Fallback if vault check fails

def execute_pacs_search():
    search_patient_id = get_a_real_patient_id()
    
    print("=" * 60)
    print(f" Initializing C-FIND Client (Query SCU)")
    print(f" Dynamic Target Patient ID: {search_patient_id}")
    print("=" * 60)

    # AE Title is 14 characters, safely adhering to the strict 16-character DICOM limit
    ae = AE(ae_title="CLINIC_WORKSTN")
    
    # Explicitly request the Patient Root Find presentation context
    ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
    
    # Construct the search payload dataset
    search_payload = Dataset()
    search_payload.QueryRetrieveLevel = "STUDY"  # Querying at the Study level
    search_payload.PatientID = search_patient_id # The filter criterion
    search_payload.PatientName = ""              # Requesting the server to return this field
    search_payload.StudyInstanceUID = ""         # Requesting the server to return this field

    # Attempt to associate with the PACS server on port 11112
    assoc = ae.associate("127.0.0.1", 11112, ae_title="SECTRA_MINI_PACS")
    
    if assoc.is_established:
        print(f"[1] Connection Established. Sending C-FIND query...\n")
        print(f"{'Matched Name':<20} | {'Matched ID':<15} | Study Instance UID")
        print("-" * 75)
        
        # Send query using the explicit SOP Class identifier to ensure acceptance
        responses = assoc.send_c_find(search_payload, query_model=PatientRootQueryRetrieveInformationModelFind)
        
        for (status, identifier) in responses:
            # Status code 0xFF00 indicates a matching record was streamed back
            if status and status.Status == 0xFF00 and identifier: 
                print(f"{str(getattr(identifier, 'PatientName', 'N/A')):<20} | {str(getattr(identifier, 'PatientID', 'N/A')):<15} | {getattr(identifier, 'StudyInstanceUID', 'N/A')}")
                
        assoc.release()
        print("-" * 75)
        print("[2] Association released cleanly.")
    else:
        print("[!] Connection rejected by PACS server. Check if MiniPacsServer.py is running.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    execute_pacs_search()