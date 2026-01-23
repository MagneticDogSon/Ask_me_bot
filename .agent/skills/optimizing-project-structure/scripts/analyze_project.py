import os
import sys
from collections import Counter
from pathlib import Path

def analyze_structure(root_path):
    root = Path(root_path)
    if not root.exists():
        print(f"Error: Path {root_path} does not exist.")
        return

    print(f"--- Project Analysis for: {root.name} ---")
    
    # 1. Root Level Clutter
    files = [f for f in root.iterdir() if f.is_file()]
    dirs = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    print(f"\n[Root Directory Stats]")
    print(f"Total Files: {len(files)}")
    print(f"Total Dirs:  {len(dirs)}")
    
    if len(files) > 5:
        print("\n[!] WARNING: Root directory contains many files. Consider moving them to src/ or docs/.")
        for f in files:
            print(f"  - {f.name}")
    else:
        print("\n[Root Files]")
        for f in files:
            print(f"  - {f.name}")

    # 2. File Type Distribution (Recursive)
    print("\n[File Type Distribution]")
    extensions = Counter()
    suspicious_files = []
    
    suspicious_patterns = ['.bak', '.old', '.tmp', 'copy', 'backup', 'temp']
    
    for root_dir, _, filenames in os.walk(root):
        if '.git' in root_dir or 'node_modules' in root_dir or '__pycache__' in root_dir:
            continue
            
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            extensions[ext] += 1
            
            # Check for suspicious files
            lower_name = filename.lower()
            if any(p in lower_name for p in suspicious_patterns):
                suspicious_files.append(os.path.join(root_dir, filename))

    for ext, count in extensions.most_common():
        print(f"  {ext or 'No Ext'}: {count}")

    # 3. Junk Detection
    if suspicious_files:
        print("\n[Potential Junk Files]")
        for f in suspicious_files:
            print(f"  - {f}")
    else:
        print("\n[Junk check] No obvious junk files found.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = os.getcwd()
    
    analyze_structure(target_dir)
