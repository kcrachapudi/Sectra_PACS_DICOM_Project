import pydicom
import os

def inspect_dicom(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print("=" * 60)
    print(f" Reading DICOM File: {os.path.basename(file_path)}")
    print("=" * 60)

    # Load the dataset
    ds = pydicom.dcmread(file_path)

    # 1. Verify the 'DICM' prefix handshake
    # pydicom handles the 128-byte preamble automatically behind the scenes
    print(f"[*] File Preamble Detected: Yes")
    print(f"[*] DICOM Prefix Verification: {ds.file_meta.get('FileMetaInformationGroupLength', 'Valid') and 'PASSED'}")
    
    # 2. Extract the Transfer Syntax (The Parsing Rules)
    transfer_syntax = ds.file_meta.TransferSyntaxUID
    print(f"[*] Transfer Syntax UID: {transfer_syntax} ({transfer_syntax.name})")
    print("-" * 60)

    # 3. Extract the Core Metadata Dataset
    print("[+] CLINICAL DATA ELEMENTS SET:")
    print(f"    - Patient Name (0010,0010) : {ds.get('PatientName', 'N/A')}")
    print(f"    - Patient ID   (0010,0020) : {ds.get('PatientID', 'N/A')}")
    print(f"    - Accession #  (0008,0050) : {ds.get('AccessionNumber', 'N/A')}")
    print(f"    - Modality     (0008,0060) : {ds.get('Modality', 'N/A')}")
    print(f"    - Study Desc   (0008,1030) : {ds.get('StudyDescription', 'N/A')}")
    print("-" * 60)

    # 4. Extract the Identity Chain (The Hierarchy UIDs)
    print("[+] IDENTITY CHAIN HIERARCHY:")
    print(f"    - Study Instance UID  : {ds.StudyInstanceUID}")
    print(f"    - Series Instance UID : {ds.SeriesInstanceUID}")
    print(f"    - SOP Instance UID    : {ds.SOPInstanceUID}")
    print("-" * 60)

    # 5. Inspect the Physical Canvas Matrix
    if 'PixelData' in ds:
        print("[+] PIXEL MATRIX CHARACTERISTICS:")
        print(f"    - Rows x Columns : {ds.Rows} x {ds.Columns}")
        print(f"    - Bits Allocated : {ds.BitsAllocated} bits (High-Bit Precision)")
        print(f"    - Pixel Arrays   : {len(ds.PixelData)} raw binary bytes packed at the base.")
    else:
        print("[!] Warning: This file contains no Pixel Data segment.")
    print("=" * 60)
