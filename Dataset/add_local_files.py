"""
Script to add Fortran/C++ file pairs from local directories to combined.parquet
"""
import os
import pandas as pd
from pathlib import Path


def main():
    # Paths
    base_dir = Path(__file__).parent
    fortran_dir = base_dir / "fortran"
    cpp_dir = base_dir / "cpp"
    parquet_path = base_dir / "combined.parquet"
    
    # Load existing data
    print(f"Loading existing data from {parquet_path}...")
    df_existing = pd.read_parquet(parquet_path)
    print(f"Existing rows: {len(df_existing)}")
    print(f"Columns: {list(df_existing.columns)}")
    
    # Collect new pairs
    new_pairs = []
    fortran_files = sorted(fortran_dir.glob("file*.f90"))
    
    print(f"\nFound {len(fortran_files)} Fortran files")
    
    for fortran_file in fortran_files:
        # Extract file number (e.g., file000.f90 -> 000)
        file_num = fortran_file.stem.replace("file", "")
        cpp_file = cpp_dir / f"file{file_num}.cpp"
        
        # Check if corresponding C++ file exists
        if not cpp_file.exists():
            print(f"Warning: Missing C++ file for {fortran_file.name}")
            continue
        
        # Read both files
        try:
            with open(fortran_file, "r", encoding="utf-8") as f:
                fortran_code = f.read()
            with open(cpp_file, "r", encoding="utf-8") as f:
                cpp_code = f.read()
            
            new_pairs.append({
                "fortran": fortran_code,
                "cpp": cpp_code
            })
        except Exception as e:
            print(f"Error reading {fortran_file.name}: {e}")
            continue
    
    print(f"\nSuccessfully read {len(new_pairs)} new pairs")
    
    # Create DataFrame from new pairs
    df_new = pd.DataFrame(new_pairs)
    
    # Combine with existing data
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    
    print(f"\nTotal rows after merge: {len(df_combined)}")
    print(f"  - Original: {len(df_existing)}")
    print(f"  - New: {len(df_new)}")
    
    # Save back to parquet
    print(f"\nSaving to {parquet_path}...")
    df_combined.to_parquet(parquet_path, index=False)
    
    print("✅ Done!")
    print(f"\nFinal dataset stats:")
    print(f"  - Total rows: {len(df_combined)}")
    print(f"  - Columns: {list(df_combined.columns)}")
    
    # Show sample lengths
    if len(df_combined) > 0:
        sample = df_combined.iloc[-1]  # Last added row
        print(f"\nSample from newly added data:")
        print(f"  - Fortran code length: {len(sample['fortran'])} chars")
        print(f"  - C++ code length: {len(sample['cpp'])} chars")


if __name__ == "__main__":
    main()
