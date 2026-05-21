import pydicom
import os

def anonymize_dicom(input_path, output_path):
    print("=" * 60)
    print(" Running Edulet 3: Cryptographic Anonymizer")
    print("=" * 60)
    
    if not os.path.exists(input_path):
        print(f"[!] Error: Source file not found at {input_path}")
        return

    print(f"[1] Loading target medical file: {os.path.basename(input_path)}")
    ds = pydicom.dcmread(input_path)
    
    # Capture original tracking parameters
    original_name = ds.get("PatientName", "UNKNOWN")
    original_uid = ds.SOPInstanceUID
    
    print(f"[2] Current Patient Identity identified as: {original_name}")
    print(f"[3] Current SOP Instance UID: {original_uid}")
    print("-" * 60)

    # Core Action: Overwrite the demographic data element tag (0010,0010)
    # Standard medical notation utilizes carets to separate name components
    ds.PatientName = "ANONYMOUS^PATIENT^001"
    
    # Ironclad Security Rule: If you alter a legal medical record, it is no longer 
    # the same historical instance. You MUST change the SOP Instance UID so a PACS 
    # doesn't accidentally overwrite the original file in its database.
    # We will safely append a unique testing suffix to this file's DNA identifier.
    ds.SOPInstanceUID = original_uid + ".1.ANON.2026"
    
    print(f"[4] Injecting replacement data into tag (0010,0010)...")
    print(f"[5] Mutating SOP Instance UID to protect data lineage...")
    print("-" * 60)

    # Save the modified binary stream down to the new path
    # pydicom automatically handles recalculating the exact byte lengths 
    # and structural padding under the hood!
    ds.save_as(output_path)
    print(f"[6] Serialization complete! Secure file written to:\n    -> {output_path}")
    print("=" * 60 + "\n")