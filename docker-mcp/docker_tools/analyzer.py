import os
import json

def find_file_and_folder(root, filenames):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f in filenames:
                return os.path.join(dirpath, f), dirpath
    return None, None

def analyze_application(app_path: str) -> dict:
    app_path = app_path.strip()
    analysis = {
        "app_path": app_path,
        "app_type": None,
        "dependencies": [],
        "entry_point": None,
        "detected_files": [],
        "status": "analyzed",
        "app_found_in": None   # New: where the app marker was found
    }

    if not os.path.exists(app_path):
        analysis["status"] = "error"
        analysis["error"] = f"Path not found: {app_path}"
        return analysis

    # Root detected_files for user info
    analysis["detected_files"] = os.listdir(app_path)

    # Recursive detection
    req_file, py_folder = find_file_and_folder(app_path, ["requirements.txt"])
    pkg_file, node_folder = find_file_and_folder(app_path, ["package.json"])
    pom_file, java_folder = find_file_and_folder(app_path, ["pom.xml"])
    gem_file, ruby_folder = find_file_and_folder(app_path, ["Gemfile"])

    if req_file:
        analysis["app_type"] = "python"
        analysis["app_found_in"] = py_folder
        analysis["entry_point"] = "main.py"  # Could make this smarter
        with open(req_file) as f:
            analysis["dependencies"] = f.read().splitlines()
    elif pkg_file:
        analysis["app_type"] = "node"
        analysis["app_found_in"] = node_folder
        analysis["entry_point"] = "index.js"
        with open(pkg_file) as f:
            pkg = json.load(f)
            analysis["dependencies"] = list(pkg.get("dependencies", {}).keys())
    elif pom_file:
        analysis["app_type"] = "java"
        analysis["app_found_in"] = java_folder
        analysis["entry_point"] = "Main.java"
    elif gem_file:
        analysis["app_type"] = "ruby"
        analysis["app_found_in"] = ruby_folder
        analysis["entry_point"] = "app.rb"
    else:
        # static detection
        html_file = None
        html_folder = None
        for dirpath, _, files in os.walk(app_path):
            for f in files:
                if f.endswith(".html"):
                    html_file = os.path.join(dirpath, f)
                    html_folder = dirpath
                    break
            if html_file:
                break
        if html_file:
            analysis["app_type"] = "static"
            analysis["app_found_in"] = html_folder
            analysis["entry_point"] = os.path.basename(html_file)
        else:
            analysis["app_type"] = "unknown"

    return analysis
