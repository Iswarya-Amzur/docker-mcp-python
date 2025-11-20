"""
Test root-level package manager priority in language detection.

This tests that when a project has a root-level package.json (Node project)
but also contains subdirectories with Java files (e.g., android/ build folder),
the language detection correctly identifies it as Node, not Java.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add docker-mcp to path
sys.path.insert(0, str(Path(__file__).parent / 'docker-mcp'))

from docker_tools.analyzer import analyze_application


def test_react_with_android_directory():
    """Test that React app with android/ directory is detected as Node, not Java."""
    print("=" * 80)
    print("TEST: React/Vite app with Android build directory")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "issue-tracker"
        project_path.mkdir()
        
        # Create root-level Node/React project files
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
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "vite": "^5.0.0",
                "@vitejs/plugin-react": "^4.0.0"
            }
        }
        
        with open(project_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create vite.config.js
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
})
"""
        with open(project_path / "vite.config.js", "w") as f:
            f.write(vite_config)
        
        # Create index.html
        with open(project_path / "index.html", "w") as f:
            f.write("<html><body><div id='root'></div></body></html>")
        
        # Create src directory with React files
        src_dir = project_path / "src"
        src_dir.mkdir()
        
        with open(src_dir / "App.jsx", "w") as f:
            f.write("export default function App() { return <div>Hello</div> }")
        
        with open(src_dir / "main.jsx", "w") as f:
            f.write("import React from 'react'\nimport ReactDOM from 'react-dom/client'")
        
        # Create android directory with Java files (simulating Capacitor build)
        android_dir = project_path / "android"
        android_dir.mkdir()
        
        # Create build.gradle
        with open(android_dir / "build.gradle", "w") as f:
            f.write("buildscript { repositories { google() } }")
        
        # Create app subdirectory with Java source files
        app_dir = android_dir / "app"
        app_dir.mkdir()
        java_dir = app_dir / "src" / "main" / "java" / "com" / "example" / "app"
        java_dir.mkdir(parents=True)
        
        # Create multiple Java files
        for i in range(5):
            with open(java_dir / f"MainActivity{i}.java", "w") as f:
                f.write(f"package com.example.app;\npublic class MainActivity{i} {{}}")
        
        # Run analysis
        print(f"\n🔍 Analyzing project at: {project_path}")
        analysis = analyze_application(str(project_path))
        
        # Display results
        print(f"\n📊 Detection Results:")
        print(f"   Language: {analysis.get('app_type', 'UNKNOWN')}")
        print(f"   Framework: {analysis.get('framework', 'UNKNOWN')}")
        print(f"   Port: {analysis.get('port', 'UNKNOWN')}")
        
        if 'language_confidence' in analysis:
            print(f"\n📈 Language Confidence Scores:")
            for lang, score in sorted(analysis['language_confidence'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {lang}: {score}")
        
        print(f"\n📁 File Counts:")
        print(f"   Node files: {analysis.get('node_file_count', 0)}")
        print(f"   Java files: {analysis.get('java_file_count', 0)}")
        
        # Validation
        print(f"\n✅ Validation:")
        
        is_node = analysis.get('app_type') == 'node'
        is_vite = analysis.get('framework') == 'vite'
        correct_port = analysis.get('port') == 5173
        
        print(f"   Language is 'node': {'✅ PASS' if is_node else '❌ FAIL'}")
        print(f"   Framework is 'vite': {'✅ PASS' if is_vite else '❌ FAIL'}")
        print(f"   Port is 5173: {'✅ PASS' if correct_port else '❌ FAIL'}")
        
        # Check that Node has higher confidence than Java
        if 'language_confidence' in analysis:
            node_score = analysis['language_confidence'].get('node', 0)
            java_score = analysis['language_confidence'].get('java', 0)
            node_wins = node_score > java_score
            print(f"   Node score > Java score: {'✅ PASS' if node_wins else '❌ FAIL'} (Node: {node_score}, Java: {java_score})")
        
        all_pass = is_node and is_vite and correct_port
        
        print(f"\n{'='*80}")
        if all_pass:
            print("✅ TEST PASSED: Root package.json correctly prioritized!")
        else:
            print("❌ TEST FAILED: Root-level package manager not prioritized correctly")
        print(f"{'='*80}\n")
        
        return all_pass


def test_java_spring_boot():
    """Test that actual Java Spring Boot project is detected as Java."""
    print("=" * 80)
    print("TEST: Java Spring Boot application")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "spring-api"
        project_path.mkdir()
        
        # Create pom.xml (Maven)
        pom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>spring-api</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
"""
        with open(project_path / "pom.xml", "w") as f:
            f.write(pom_xml)
        
        # Create src/main/java directory with Java files
        java_dir = project_path / "src" / "main" / "java" / "com" / "example" / "api"
        java_dir.mkdir(parents=True)
        
        with open(java_dir / "Application.java", "w") as f:
            f.write("package com.example.api;\npublic class Application { public static void main(String[] args) {} }")
        
        with open(java_dir / "Controller.java", "w") as f:
            f.write("package com.example.api;\npublic class Controller {}")
        
        # Run analysis
        print(f"\n🔍 Analyzing project at: {project_path}")
        analysis = analyze_application(str(project_path))
        
        # Display results
        print(f"\n📊 Detection Results:")
        print(f"   Language: {analysis.get('app_type', 'UNKNOWN')}")
        print(f"   Framework: {analysis.get('framework', 'UNKNOWN')}")
        print(f"   Port: {analysis.get('port', 'UNKNOWN')}")
        
        # Validation
        is_java = analysis.get('app_type') == 'java'
        print(f"\n✅ Validation:")
        print(f"   Language is 'java': {'✅ PASS' if is_java else '❌ FAIL'}")
        
        print(f"\n{'='*80}")
        if is_java:
            print("✅ TEST PASSED: Java Spring Boot correctly detected!")
        else:
            print("❌ TEST FAILED: Java project not detected correctly")
        print(f"{'='*80}\n")
        
        return is_java


if __name__ == "__main__":
    print("\n🚀 Testing Root-Level Package Manager Priority\n")
    
    test1_pass = test_react_with_android_directory()
    test2_pass = test_java_spring_boot()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total = 2
    passed = sum([test1_pass, test2_pass])
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Root language priority works correctly!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Root language detection needs fixes")
        sys.exit(1)
