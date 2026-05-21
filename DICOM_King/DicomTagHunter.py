import pydicom

def hunt_tags(file_path):
    # Load the target dataset
    ds = pydicom.dcmread(file_path)
    
    print("\n" + "=" * 75)
    print(f" SECURE HEXADECIMAL TAG HUNTER REPORT FOR: {file_path}")
    print("=" * 75)
    print(f"{'Hex Tag':<15} | {'VR':<4} | {'Length':<8} | {'Attribute Name':<25} | Value")
    print("-" * 75)

    # Loop through every single element inside the DICOM body dataset
    for element in ds:
        # 1. Format the group and element numbers into standard (GGGG,EEEE) hex notations
        tag_str = f"({element.tag.group:04X},{element.tag.element:04X})"
        
        # 2. FIXED: Try modern .value_length first, fall back to legacy .length if needed
        raw_length = getattr(element, 'value_length', getattr(element, 'length', 'N/A'))
        len_str = str(raw_length)
        
        # 3. Truncate long values (like raw pixel bits) so they don't break the terminal layout
        val_display = str(element.value)
        if len(val_display) > 35:
            val_display = val_display[:32] + "..."

        # 4. Print the safely explicitly converted string components
        print(f"{tag_str:<15} | {element.VR:<4} | {len_str:<8} | {element.name[:25]:<25} | {val_display}")
    
    print("=" * 75 + "\n")