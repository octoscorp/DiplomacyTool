"""
A quick helper script to make manually inputting ranges to JSON files faster.
Runs a replace-all of @@<start>-<end>@ with <start>, <start+1>...<end>.
"""

filepath = input("Filepath to JSON: ")
file = open(filepath, "r")
lines = ''.join(file.readlines())
file.close()

# Perform replacement
parts = lines.split('@@')
output_lines = parts[0]
for i in range(1, len(parts)):
    keyword, trail = parts[i].split('@', 1)
    start, end = keyword.split('-', 1)
    step = 1 if int(start) <= int(end) else -1

    for j in range(int(start), int(end), step):
        output_lines += f'{j},'
    output_lines += f'{end}{trail}'

# Update file
file = open(filepath, 'w')
file.write(output_lines)
file.close()