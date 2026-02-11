"""
Identify and fix problematic Unicode characters in desktop_app.py on line ~726 and ~731
"""
with open('desktop_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show the exact codepoints around lines 726 and 731 (0-indexed: 725, 730)
for lineno in [725, 730]:
    line = lines[lineno]
    print(f"Line {lineno+1}: {repr(line)}")
    for i, ch in enumerate(line):
        if ord(ch) > 127:
            print(f"  pos {i}: U+{ord(ch):04X} = {ch!r}")
