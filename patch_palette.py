with open(".jules/palette.md", "r") as f:
    lines = f.readlines()
# Remove English version that I just added
new_lines = lines[:-5]
with open(".jules/palette.md", "w") as f:
    f.writelines(new_lines)
