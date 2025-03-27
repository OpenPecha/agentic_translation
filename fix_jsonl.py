#!/usr/bin/env python
"""
Fix invalid JSONL file by:
1. Reading each line
2. Parsing JSON
3. Writing valid JSON back to a new file
"""

import json
import sys
from pathlib import Path

def fix_jsonl(input_file, output_file=None):
    """Fix invalid JSONL file."""
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_fixed.jsonl"
    
    print(f"Fixing {input_file} and saving to {output_file}")
    
    valid_lines = 0
    invalid_lines = 0
    fixed_lines = 0
    
    with open(input_file, 'r', encoding='utf-8') as in_f:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for i, line in enumerate(in_f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    # Try to parse the JSON
                    data = json.loads(line)
                    # Write valid JSON back
                    json.dump(data, out_f, ensure_ascii=False)
                    out_f.write('\n')
                    valid_lines += 1
                except json.JSONDecodeError as e:
                    invalid_lines += 1
                    print(f"Invalid JSON on line {i}: {str(e)}")
                    print(f"Line content (first 100 chars): {line[:100]}...")
                    
                    # Try to fix common issues and parse again
                    try:
                        # Some common fixes: handle trailing commas, fix quotes
                        fixed_line = line.replace(",}", "}").replace(",]", "]")
                        data = json.loads(fixed_line)
                        json.dump(data, out_f, ensure_ascii=False)
                        out_f.write('\n')
                        fixed_lines += 1
                        print(f"  ✓ Fixed successfully")
                    except Exception as fix_e:
                        print(f"  ✗ Could not fix: {str(fix_e)}")
    
    print(f"\nResults:")
    print(f"  Valid lines: {valid_lines}")
    print(f"  Invalid lines: {invalid_lines}")
    print(f"  Fixed lines: {fixed_lines}")
    print(f"  Total processed: {valid_lines + invalid_lines}")
    
    if invalid_lines == 0 or fixed_lines == invalid_lines:
        print(f"\n✅ All lines are now valid JSON!")
        return True
    else:
        print(f"\n⚠️ Some lines could not be fixed ({invalid_lines - fixed_lines}).")
        print(f"   You may need to manually edit these lines.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_jsonl.py input_file.jsonl [output_file.jsonl]")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    success = fix_jsonl(input_file, output_file)
    sys.exit(0 if success else 1)