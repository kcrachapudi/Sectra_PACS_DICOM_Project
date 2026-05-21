import DicomInspector, DicomTagHunter, DicomAnonymizer

def GetSampleDicomPath():
    # This function can be expanded to allow user input or dynamic path retrieval
    return "Dicom-Test-Files/MR_small.dcm"

def GetAnonymizedOutputPath(sample_dicom_path):
    # This function can be expanded to allow user input or dynamic path retrieval
    # Add _anynomized suffix to the original filename for clarity
    base_name = sample_dicom_path.rsplit('.', 1)[0]  # Remove the file extension
    return f"{base_name}_anonymized.dcm"



def Run():
    # Point to Sample DICOM files in the DICOM-Test-Files directory
    sample_dicom_path = GetSampleDicomPath()

    DicomInspector.inspect_dicom(sample_dicom_path)

    DicomTagHunter.hunt_tags(sample_dicom_path)

    anonymized_output_path = GetAnonymizedOutputPath(sample_dicom_path)
    print(f"Running DICOM anonymization process. Input: {sample_dicom_path}, Output: {anonymized_output_path}.\n")
    DicomAnonymizer.anonymize_dicom(sample_dicom_path, anonymized_output_path)
    print("\nNow running tag hunting on the newly anonymized file to confirm changes...\n")
    DicomTagHunter.hunt_tags(anonymized_output_path)

    
if __name__ == "__main__":
    print("Starting DICOM Examiner...\n")

    Run()

    print("DICOM examination complete. All operations executed successfully.")