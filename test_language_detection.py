"""
Test language and port detection improvements.
"""
import sys
import os
from pathlib import Path
import json

# Add docker-mcp directory to path
current_dir = Path(__file__).parent
docker_mcp_dir = current_dir / 'docker-mcp'
sys.path.insert(0, str(docker_mcp_dir))

from docker_tools.analyzer import analyze_application

def create_test_project(base_path: Path, project_type: str):
    """Create a test project structure."""
    project_path = base_path / f"test_{project_type}"
    project_path.mkdir(exist_ok=True)
    
    if project_type == "python_flask":
        # Create Python Flask project
        (project_path / "requirements.txt").write_text("flask==2.3.0\ngunicorn==20.1.0\n")
        (project_path / "app.py").write_text("""
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""")
    
    elif project_type == "node_express":
        # Create Node.js Express project
        pkg = {
            "name": "test-express",
            "version": "1.0.0",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js"
            },
            "dependencies": {
                "express": "^4.18.0"
            }
        }
        (project_path / "package.json").write_text(json.dumps(pkg, indent=2))
        (project_path / "server.js").write_text("""
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
""")
    
    elif project_type == "react_vite":
        # Create React + Vite project
        pkg = {
            "name": "test-react",
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
                "@vitejs/plugin-react": "^4.0.0",
                "vite": "^4.3.0"
            }
        }
        (project_path / "package.json").write_text(json.dumps(pkg, indent=2))
        (project_path / "vite.config.js").write_text("""
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
})
""")
        (project_path / "index.html").write_text("<html><body><div id='root'></div></body></html>")
        src_dir = project_path / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "App.jsx").write_text("export default function App() { return <h1>Hello</h1> }")
    
    return project_path

def test_language_detection():
    """Test language and port detection."""
    print(f"\n{'='*100}")
    print("🧪 TESTING LANGUAGE & PORT DETECTION")
    print(f"{'='*100}\n")
    
    temp_dir = Path("temp_test_projects")
    temp_dir.mkdir(exist_ok=True)
    
    test_cases = [
        ("python_flask", "python", "flask", 5000),
        ("node_express", "node", "express", 3000),
        ("react_vite", "node", "vite", 5173),
    ]
    
    results = []
    
    for project_type, expected_lang, expected_framework, expected_port in test_cases:
        print(f"📝 Testing: {project_type}")
        print("-" * 80)
        
        # Create test project
        project_path = create_test_project(temp_dir, project_type)
        
        # Analyze
        analysis = analyze_application(str(project_path))
        
        # Check results
        detected_lang = analysis.get('app_type', 'unknown')
        detected_framework = analysis.get('framework', 'unknown')
        detected_port = analysis.get('port', 0)
        
        print(f"  Expected:  Language={expected_lang}, Framework={expected_framework}, Port={expected_port}")
        print(f"  Detected:  Language={detected_lang}, Framework={detected_framework}, Port={detected_port}")
        
        # Validation
        lang_ok = detected_lang == expected_lang
        framework_ok = detected_framework == expected_framework
        port_ok = detected_port == expected_port
        
        print(f"  Language:  {'✅' if lang_ok else '❌'}")
        print(f"  Framework: {'✅' if framework_ok else '❌'}")
        print(f"  Port:      {'✅' if port_ok else '❌'}")
        
        if analysis.get('language_confidence'):
            print(f"  Confidence: {analysis['language_confidence']}")
        
        results.append({
            'project': project_type,
            'lang_ok': lang_ok,
            'framework_ok': framework_ok,
            'port_ok': port_ok,
            'all_ok': lang_ok and framework_ok and port_ok
        })
        
        print()
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Summary
    print(f"{'='*100}")
    print("📊 SUMMARY")
    print(f"{'='*100}\n")
    
    for result in results:
        status = "✅ PASS" if result['all_ok'] else "❌ FAIL"
        print(f"{status}: {result['project']}")
        if not result['all_ok']:
            if not result['lang_ok']:
                print(f"  - Language detection failed")
            if not result['framework_ok']:
                print(f"  - Framework detection failed")
            if not result['port_ok']:
                print(f"  - Port detection failed")
    
    total = len(results)
    passed = sum(1 for r in results if r['all_ok'])
    
    print(f"\n{passed}/{total} tests passed")
    print(f"{'='*100}\n")
    
    return passed == total

if __name__ == "__main__":
    success = test_language_detection()
    sys.exit(0 if success else 1)
