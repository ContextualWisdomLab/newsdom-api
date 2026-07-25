import re
with open(".trivyignore", "r") as f:
    code = f.read()

lines = code.split("\n")
new_lines = []
for line in lines:
    if line.startswith("DS-0002"):
        pass
    new_lines.append(line)
