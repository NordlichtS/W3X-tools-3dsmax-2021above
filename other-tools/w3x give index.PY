#!/usr/bin/env python3
import re

def modify_xml_in_place(file_path):
    """
    Reads the file as plain text and appends an index comment at the end of
    each line that starts (ignoring indentation) with <Pivot Name=

    The comment is appended to the end of the line so that the overall
    line count remains unchanged.
    """
    # Read all lines from the file.
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Regex pattern: line starts (ignoring whitespace) with <Pivot Name=
    pivot_regex = re.compile(r'^\s*<Pivot Name=')
    
    new_lines = []
    pivot_counter = 0

    for line in lines:
        if pivot_regex.search(line):
            # Append the comment " <!-- {index} -->" at the end of the line (before the newline).
            line = line.rstrip("\n") + f" <!-- {pivot_counter} -->\n"
            pivot_counter += 1
        new_lines.append(line)
    
    # Write the modified lines back to the same file.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\nModified file saved in-place: {file_path}")

if __name__ == '__main__':
    print("this script will add index comment for pivot in w3x")

    print("Please drag and drop your .w3x file into this window, then press Enter:")
    file_path = input().strip()
    
    # Remove surrounding quotes if present (drag and drop on Windows may add them)
    if file_path.startswith('"') and file_path.endswith('"'):
        file_path = file_path[1:-1]
    
    if not file_path:
        print("No file provided. Exiting.")
    else:
        try:
            modify_xml_in_place(file_path)
            print("\nFile processed successfully.")
        except Exception as e:
            print("\nAn error occurred:", e)
    
    input("\nPress Enter to exit.")
