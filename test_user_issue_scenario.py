"""
Test the exact scenario from the user's issue:
issue-tracker with package.json, vite.config, and android/ subdirectory.
"""

import tempfile
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / 'docker-mcp'))

from docker_tools.analyzer import analyze_application


def test_issue_tracker_scenario():
    """Simulate the exact issue-tracker project structure."""
    print("=" * 80)
    print("TEST: User's issue-tracker project structure")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "issue-tracker"
        project_path.mkdir()
        
        # Create all the root-level files mentioned in the user's JSON
        files_to_create = [
            ".env",
            "capacitor.config.ts",
            "index.html",
            "package.json",
            "package-lock.json",
            "vite.config.js",
            "postcss.config.cjs",
            "tailwind.config.js",
            "README.md"
        ]
        
        # Create package.json (Node project)
        package_json = {
            "name": "issue-tracker",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@capacitor/core": "^5.0.0",
                "@capacitor/android": "^5.0.0"
            },
            "devDependencies": {
                "vite": "^5.0.0",
                "@vitejs/plugin-react": "^4.0.0",
                "tailwindcss": "^3.0.0"
            }
        }
        
        with open(project_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create other files
        with open(project_path / "vite.config.js", "w") as f:
            f.write("import { defineConfig } from 'vite'\nexport default defineConfig({})")
        
        with open(project_path / "capacitor.config.ts", "w") as f:
            f.write("import { CapacitorConfig } from '@capacitor/cli'\nconst config: CapacitorConfig = {}")
        
        with open(project_path / "index.html", "w") as f:
            f.write("<html><body><div id='root'></div></body></html>")
        
        with open(project_path / "tailwind.config.js", "w") as f:
            f.write("module.exports = { content: ['./src/**/*.{js,jsx}'] }")
        
        # Create src directory with React components
        src_dir = project_path / "src"
        src_dir.mkdir()
        
        with open(src_dir / "App.jsx", "w") as f:
            f.write("export default function App() { return <div>Issue Tracker</div> }")
        
        with open(src_dir / "main.jsx", "w") as f:
            f.write("import React from 'react'\nimport ReactDOM from 'react-dom/client'")
        
        # Create android directory (Capacitor build output)
        android_dir = project_path / "android"
        android_dir.mkdir()
        
        # Create build.gradle
        with open(android_dir / "build.gradle", "w") as f:
            f.write("""buildscript {
    repositories {
        google()
        mavenCentral()
    }
}""")
        
        # Create gradle.properties
        with open(android_dir / "gradle.properties", "w") as f:
            f.write("android.useAndroidX=true")
        
        # Create app subdirectory
        app_dir = android_dir / "app"
        app_dir.mkdir()
        
        with open(app_dir / "build.gradle", "w") as f:
            f.write("apply plugin: 'com.android.application'")
        
        # Create Java source files (like in the user's output)
        java_dir = app_dir / "src" / "main" / "java" / "com" / "amzur" / "itracker"
        java_dir.mkdir(parents=True)
        
        java_files = [
            "MainActivity.java",
            "MyFirebaseMessagingService.java",
            "NotificationListService.java",
            "StatusUpdateActivity.java"
        ]
        
        for java_file in java_files:
            with open(java_dir / java_file, "w") as f:
                class_name = java_file.replace(".java", "")
                f.write(f"""package com.amzur.itracker;

public class {class_name} {{
    // Android activity
}}
""")
        
        # Create capacitor-cordova-android-plugins (mentioned in user's output)
        plugins_dir = android_dir / "capacitor-cordova-android-plugins"
        plugins_dir.mkdir()
        
        with open(plugins_dir / "build.gradle", "w") as f:
            f.write("apply plugin: 'com.android.library'")
        
        print(f"\n📁 Created project structure:")
        print(f"   Root: {project_path}")
        print(f"   - package.json (Node)")
        print(f"   - vite.config.js (Vite)")
        print(f"   - capacitor.config.ts (Capacitor)")
        print(f"   - src/App.jsx (React)")
        print(f"   - android/app/src/main/java/.../MainActivity.java (4 Java files)")
        
        # Run analysis
        print(f"\n🔍 Analyzing project...")
        analysis = analyze_application(str(project_path))
        
        # Display results
        print(f"\n{'='*80}")
        print("📊 DETECTION RESULTS")
        print(f"{'='*80}")
        print(f"Language:  {analysis.get('app_type', 'UNKNOWN')}")
        print(f"Framework: {analysis.get('framework', 'UNKNOWN')}")
        print(f"Port:      {analysis.get('port', 'UNKNOWN')}")
        print(f"Status:    {analysis.get('status', 'UNKNOWN')}")
        
        if 'language_confidence' in analysis:
            print(f"\n📈 Language Confidence Scores:")
            for lang, score in sorted(analysis['language_confidence'].items(), key=lambda x: x[1], reverse=True):
                emoji = "🏆" if lang == analysis.get('app_type') else "  "
                print(f"   {emoji} {lang}: {score}")
        
        print(f"\n📁 File Counts:")
        print(f"   Node files: {analysis.get('node_file_count', 0)}")
        print(f"   Java files: {analysis.get('java_file_count', 0)}")
        
        if 'detected_files' in analysis and analysis['detected_files']:
            print(f"   Total detected files: {len(analysis['detected_files'])}")
        
        # Validation
        print(f"\n{'='*80}")
        print("✅ VALIDATION")
        print(f"{'='*80}")
        
        checks = {
            "Language is 'node'": analysis.get('app_type') == 'node',
            "Framework is 'vite'": analysis.get('framework') == 'vite',
            "Port is 5173": analysis.get('port') == 5173,
            "Status is 'completed'": analysis.get('status') == 'completed',
        }
        
        # Check confidence scores
        if 'language_confidence' in analysis:
            node_score = analysis['language_confidence'].get('node', 0)
            java_score = analysis['language_confidence'].get('java', 0)
            checks["Node score > Java score"] = node_score > java_score
            checks["Node score >= 1000"] = node_score >= 1000
        
        all_pass = True
        for check_name, result in checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {check_name}")
            if not result:
                all_pass = False
        
        # Summary
        print(f"\n{'='*80}")
        if all_pass:
            print("✅ TEST PASSED")
            print("The issue-tracker project is correctly detected as Node/Vite,")
            print("not Java, despite having an android/ subdirectory!")
        else:
            print("❌ TEST FAILED")
            print("Language detection still incorrectly identifies Java over Node")
        print(f"{'='*80}\n")
        
        return all_pass


if __name__ == "__main__":
    print("\n🧪 Testing User's Exact Scenario: issue-tracker with android/\n")
    
    success = test_issue_tracker_scenario()
    
    if success:
        print("\n✅ User's issue is FIXED!")
        print("React/Vite apps with Capacitor android/ builds are now correctly detected.")
        sys.exit(0)
    else:
        print("\n❌ User's issue still exists")
        sys.exit(1)
