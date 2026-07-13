with open("Dockerfile.test", "r") as f:
    content = f.read()

if "USER jules" not in content:
    content = content.replace('CMD ["pytest"]', 'RUN useradd -m jules && chown -R jules:jules /app\nUSER jules\nCMD ["pytest"]')
    with open("Dockerfile.test", "w") as f:
        f.write(content)
