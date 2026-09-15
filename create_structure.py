import os

# Define the folder structure
structure = {
    "mcq-quiz-platform": {
        "files": [
            "app.py",
            "requirements.txt",
            "Procfile",
            "railway.json",
        ],
        "folders": {
            "templates": {
                "files": [
                    "base.html",
                    "login.html",
                    "admin_dashboard.html",
                    "user_dashboard.html",
                    "quiz.html",
                    "result.html",
                    "leaderboard.html",
                ],
                "folders": {},
            },
            "static": {
                "files": [],
                "folders": {
                    "css": {"files": ["style.css"], "folders": {}},
                    "js": {"files": ["quiz.js"], "folders": {}},
                },
            },
        },
    }
}


def create_structure(base_path, node):
    """Recursively create folders and files."""
    os.makedirs(base_path, exist_ok=True)

    # Create files
    for file_name in node.get("files", []):
        file_path = os.path.join(base_path, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")  # create empty file
        print(f"Created file:  {file_path}")

    # Create nested folders
    for folder_name, child in node.get("folders", {}).items():
        folder_path = os.path.join(base_path, folder_name)
        create_structure(folder_path, child)


if __name__ == "__main__":
    root_name = list(structure.keys())[0]
    root_data = structure[root_name]
    create_structure(root_name, root_data)
    print(f"\n✅ Folder structure '{root_name}' created successfully!")