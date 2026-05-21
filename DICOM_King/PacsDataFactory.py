import os
import pydicom
from pydicom.uid import generate_uid

def generate_mock_pacs_data(template_path, storage_dir):
    print("=" * 60)
    print(" Running PacsDataFactory: Generating 125 Unique Files")
    print("=" * 60)
    
    if not os.path.exists(template_path):
        print(f"[!] Error: Template file not found at {template_path}")
        return

    # Load our template file as a base
    ds = pydicom.dcmread(template_path)
    
    total_files_generated = 0

    # 1. Loop through 5 Patients
    for p_idx in range(1, 6):
        patient_name = f"DOE^PATIENT^00{p_idx}"
        patient_id = f"PATIENT_ID_00{p_idx}"
        
        # 2. Loop through 5 Encounters / Studies per patient
        for s_idx in range(1, 6):
            # Generate a globally unique Study Instance UID for this encounter
            study_uid = generate_uid()
            study_desc = f"MRI Brain Encounter {s_idx}"
            accession_num = f"ACC-2026-{p_idx}{s_idx}"
            
            # Create a Series Instance UID for the images in this study
            series_uid = generate_uid()
            
            # Create the physical folder path in the vault to mimic our server routing
            study_folder = os.path.join(storage_dir, patient_id, study_uid)
            os.makedirs(study_folder, exist_ok=True)
            
            # 3. Loop through 5 individual image slices (Instances) per study
            for i_idx in range(1, 6):
                # Generate a completely unique SOP Instance UID for this specific file
                sop_instance_uid = generate_uid()
                
                # Mutate the metadata tags in memory
                ds.PatientName = patient_name
                ds.PatientID = patient_id
                ds.StudyInstanceUID = study_uid
                ds.SeriesInstanceUID = series_uid
                ds.SOPInstanceUID = sop_instance_uid
                ds.StudyDescription = study_desc
                ds.AccessionNumber = accession_num
                ds.InstanceNumber = str(i_idx)
                
                # Build filename and serialize the new binary object directly to disk
                filename = os.path.join(study_folder, f"{sop_instance_uid}.dcm")
                ds.save_as(filename, write_like_original=False)
                
                total_files_generated += 1

    print(f"[✔] Success! Generated {total_files_generated} structured DICOM files.")
    print(f"    Vault populated at: {storage_dir}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    template = "Dicom-Test-Files/MR_small_anonymized.dcm"
    vault = "/home/augustus/Projects/Sectra_PACS_DICOM_Project/DICOM_King/Pacs_Vault"
    generate_mock_pacs_data(template, vault)