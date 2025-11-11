#!/usr/bin/env python3
"""
Docker MCP Server Installation and Configuration Script

This script:
1. Installs the Docker MCP server package
2. Automatically detects the IDE/MCP client being used
3. Updates the appropriate configuration file
4. Provides setup instructions

Usage:
    python install.py [--ide claude|vscode|all]
"""

import os
import sys
import json
import argparse
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional


class MCPInstaller:
    """Handles installation and configuration of Docker MCP server"""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        self.configs = self._get_config_paths()
        
    def _get_config_paths(self) -> Dict[str, Path]:
        """Get configuration file paths for different IDEs"""
        configs = {}
        
        # Claude Desktop
        if self.system == "Windows":
            configs["claude"] = self.home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif self.system == "Darwin":  # macOS
            configs["claude"] = self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            configs["claude"] = self.home / ".config" / "Claude" / "claude_desktop_config.json"
        
        # VS Code (current workspace)
        # Note: This will be relative to where the script is run
        configs["vscode"] = Path.cwd() / ".vscode" / "mcp.json"
        
        return configs
    
    def install_package(self) -> bool:
        """Install the Docker MCP package"""
        print("📦 Installing Docker MCP Server...")
        try:
            # Install in development mode
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Package installed successfully")
                return True
            else:
                print(f"❌ Installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error during installation: {str(e)}")
            return False
    
    def get_python_path(self) -> str:
        """Get the full path to Python executable"""
        return sys.executable
    
    def get_server_path(self) -> str:
        """Get the full path to server.py"""
        # After pip install, we can use the entry point or direct path
        server_path = Path(__file__).parent / "docker-mcp" / "server.py"
        return str(server_path.absolute())
    
    def create_claude_config(self) -> Dict:
        """Create Claude Desktop MCP configuration"""
        return {
            "mcpServers": {
                "docker-mcp": {
                    "command": self.get_python_path(),
                    "args": [self.get_server_path()]
                }
            }
        }
    
    def create_vscode_config(self) -> Dict:
        """Create VS Code MCP configuration"""
        return {
            "servers": {
                "docker-mcp": {
                    "type": "stdio",
                    "command": self.get_python_path(),
                    "args": [self.get_server_path()],
                    "cwd": str(Path(self.get_server_path()).parent)
                }
            }
        }
    
    def update_config(self, ide: str) -> bool:
        """Update configuration file for specified IDE"""
        config_path = self.configs.get(ide)
        
        if not config_path:
            print(f"⚠️  Unknown IDE: {ide}")
            return False
        
        print(f"\n🔧 Configuring {ide.upper()}...")
        
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing config or create new
        existing_config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                print(f"📄 Found existing config at {config_path}")
            except json.JSONDecodeError:
                print(f"⚠️  Existing config is invalid JSON, will backup and recreate")
                backup_path = config_path.with_suffix('.json.backup')
                if config_path.exists():
                    config_path.rename(backup_path)
                    print(f"💾 Backed up to {backup_path}")
        
        # Merge with new config
        if ide == "claude":
            new_config = self.create_claude_config()
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            existing_config["mcpServers"]["docker-mcp"] = new_config["mcpServers"]["docker-mcp"]
        elif ide == "vscode":
            new_config = self.create_vscode_config()
            if "servers" not in existing_config:
                existing_config["servers"] = {}
            existing_config["servers"]["docker-mcp"] = new_config["servers"]["docker-mcp"]
        
        # Write updated config
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2)
            print(f"✅ Configuration updated at {config_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to write config: {str(e)}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that the installation was successful"""
        print("\n🔍 Verifying installation...")
        
        # Check if server.py is accessible
        server_path = Path(self.get_server_path())
        if not server_path.exists():
            print(f"❌ Server file not found at {server_path}")
            return False
        
        print(f"✅ Server file found: {server_path}")
        
        # Check if dependencies are installed
        try:
            import fastmcp
            import docker
            print("✅ Dependencies verified")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {str(e)}")
            return False
    
    def print_next_steps(self, configured_ides):
        """Print instructions for next steps"""
        print("\n" + "=" * 60)
        print("🎉 INSTALLATION COMPLETE!")
        print("=" * 60)
        
        if "claude" in configured_ides:
            print("\n📱 CLAUDE DESKTOP:")
            print("   1. Restart Claude Desktop application")
            print("   2. The Docker MCP server will be available automatically")
            print("   3. Try: 'dockerize my application and show me the logs'")
        
        if "vscode" in configured_ides:
            print("\n💻 VS CODE:")
            print("   1. Reload VS Code window (Ctrl+Shift+P → 'Reload Window')")
            print("   2. Open the MCP panel")
            print("   3. Docker MCP should be listed")
        
        print("\n📚 DOCUMENTATION:")
        print("   - README.md - Full documentation")
        print("   - WORKFLOW_GUIDE.md - Smart workflow guide")
        print("   - ARCHITECTURE.md - System architecture")
        
        print("\n🚀 QUICK START:")
        print("   Use the smart workflow tool: show_app_logs(project_root='your/path')")
        print("   This will:")
        print("   ✅ Analyze your application")
        print("   ✅ Dockerize if needed")
        print("   ✅ Setup monitoring (Grafana + Loki + Promtail)")
        print("   ✅ Launch dashboard in browser")
        print("   ✅ Verify logs are flowing")
        
        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Install and configure Docker MCP Server"
    )
    parser.add_argument(
        "--ide",
        choices=["claude", "vscode", "all"],
        default="all",
        help="IDE to configure (default: all)"
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip package installation, only update config"
    )
    
    args = parser.parse_args()
    
    print("🐳 Docker MCP Server Installer")
    print("=" * 60)
    
    installer = MCPInstaller()
    
    # Step 1: Install package
    if not args.skip_install:
        if not installer.install_package():
            print("\n❌ Installation failed. Please check errors above.")
            sys.exit(1)
    else:
        print("⏭️  Skipping package installation")
    
    # Step 2: Verify installation
    if not installer.verify_installation():
        print("\n❌ Installation verification failed.")
        sys.exit(1)
    
    # Step 3: Configure IDE(s)
    configured_ides = []
    
    if args.ide == "all":
        for ide in ["claude", "vscode"]:
            if installer.update_config(ide):
                configured_ides.append(ide)
    else:
        if installer.update_config(args.ide):
            configured_ides.append(args.ide)
    
    if not configured_ides:
        print("\n❌ No configurations were updated.")
        sys.exit(1)
    
    # Step 4: Print next steps
    installer.print_next_steps(configured_ides)
    
    print("\n✅ Installation complete!")


if __name__ == "__main__":
    main()
