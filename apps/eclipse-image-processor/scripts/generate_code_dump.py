#!/usr/bin/env python3
"""
Generate a text file containing the project Python source.
Usage: python3 scripts/generate_code_dump.py
"""

import os

def generate_code_dump(project_root=".", output_file="project_code_dump.txt"):
    """
    Write all discovered Python source files into a single text document.

    Args:
        project_root: Project root directory
        output_file: Output text filename
    """

    py_files = []

    # Find Python source files.
    for root, dirs, files in os.walk(project_root):
        # Skip environment and version-control directories.
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', '.env']]

        for file in sorted(files):
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                py_files.append(filepath)

    # Sort source files by path for reproducible ordering.
    py_files.sort()

    # Write the combined output file.
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("=" * 80 + "\n")
        out.write("COMPLETE PROJECT CODE DUMP\n")
        out.write("=" * 80 + "\n\n")
        out.write(f"Total Python files: {len(py_files)}\n\n")

        for filepath in py_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Write the source-file header.
                out.write("\n" + "=" * 80 + "\n")
                out.write(f"FILE: {filepath}\n")
                out.write("=" * 80 + "\n\n")

                # Copy the original source text without modification.
                out.write(content)
                out.write("\n\n")

                print(f"✓ {filepath}")

            except Exception as e:
                print(f"✗ {filepath} - Error: {e}")

    print(f"\n✅ Generated file: {output_file}")
    print(f"📊 Total files: {len(py_files)}")

    # Report the resulting file size.
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"📁 Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    # Run from the project root directory.
    project_root = "."
    output_file = "project_code_dump.txt"

    print(f"Generating source dump from: {project_root}")
    print(f"Output file: {output_file}\n")

    generate_code_dump(project_root, output_file)
