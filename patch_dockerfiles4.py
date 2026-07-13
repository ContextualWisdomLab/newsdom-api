with open(".clusterfuzzlite/Dockerfile", "r") as f:
    content = f.read()

if "USER jules" not in content:
    content += '\nRUN useradd -m jules\nUSER jules'
    with open(".clusterfuzzlite/Dockerfile", "w") as f:
        f.write(content)
