import os

# Fix app.py
if os.path.exists("app.py"):
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    # Convert tabs to 4 spaces
    content = content.replace("\t", "    ")
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed app.py")

# Fix all files in checkers/
if os.path.exists("checkers"):
    for filename in os.listdir("checkers"):
        if filename.endswith(".py"):
            path = os.path.join("checkers", filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("\t", "    ")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print("Fixed checkers/" + filename)

# Fix templates
if os.path.exists("templates"):
    for filename in os.listdir("templates"):
        if filename.endswith(".html"):
            path = os.path.join("templates", filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("\t", "    ")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print("Fixed templates/" + filename)

print()
print("All files fixed. Now run: python app.py")