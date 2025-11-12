# Docker MCP Server - Easy Installation Guide

## 🚀 Quick Install (Automated)

### Option 1: One-Command Install (Recommended)

```bash
# Clone and install automatically
git clone https://github.com/Iswarya-Amzur/docker-mcp-python.git
cd docker-mcp-python/docker-mcp
python install.py
```

This will:
- ✅ Install the package and dependencies
- ✅ Auto-detect Claude Desktop and/or VS Code
- ✅ Update configuration files automatically
- ✅ Verify the installation

### Option 2: Specify IDE

```bash
# For Claude Desktop only
python install.py --ide claude

# For VS Code only
python install.py --ide vscode

# For both (default)
python install.py --ide all
```

### Option 3: PyPI Installation (Future)

Once published to PyPI, you'll be able to install with:

```bash
pip install docker-mcp-server

# Then run the config installer
docker-mcp-install
```

## 📋 What the Installer Does

1. **Installs Dependencies**
   - FastMCP (>=0.1.0)
   - Docker SDK (>=7.0.0)
   - Playwright (>=1.40.0)
   - All other requirements

2. **Auto-Detects IDE Configuration Paths**
   - **Windows Claude**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS Claude**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux Claude**: `~/.config/Claude/claude_desktop_config.json`
   - **VS Code**: `.vscode/mcp.json` in current workspace

3. **Updates Configuration Files**
   - Reads existing config (if any)
   - Adds Docker MCP server configuration
   - Preserves other MCP servers
   - Creates backup of existing config

4. **Verifies Installation**
   - Checks server.py exists
   - Verifies all dependencies installed
   - Tests Python path resolution

## 🛠️ Manual Installation (If Needed)

If the automated installer doesn't work, you can install manually:

### Step 1: Install Package

```bash
cd docker-mcp-python/docker-mcp
pip install -r requirements.txt
```

### Step 2: Configure IDE Manually

#### For Claude Desktop:

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or equivalent:

```json
{
  "mcpServers": {
    "docker-mcp": {
      "command": "python",
      "args": [
        "C:\\path\\to\\docker-mcp-python\\docker-mcp\\docker-mcp\\server.py"
      ]
    }
  }
}
```

#### For VS Code:

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "docker-mcp": {
      "type": "stdio",
      "command": "python",
      "args": ["C:\\path\\to\\docker-mcp-python\\docker-mcp\\docker-mcp\\server.py"],
      "cwd": "C:\\path\\to\\docker-mcp-python\\docker-mcp\\docker-mcp"
    }
  }
}
```

## 🔄 Updating Configuration Only

If you've already installed but need to update config:

```bash
python install.py --skip-install
```

## 🧪 Testing the Installation

After installation, test it:

### In Claude Desktop:

```
Can you list the Docker MCP tools available?
```

Expected response: List of 20 tools

### In VS Code:

Open the MCP panel and verify "docker-mcp" appears in the server list.

## 🚀 Using the MCP

Once installed, try the smart workflow:

```
dockerize my application and show me the logs in grafana dashboard
```

Or use specific tools:

```
# Analyze an application
analyze_app(app_path="C:\\MyProject")

# Show logs intelligently
show_app_logs(project_root="C:\\MyProject")

# Setup monitoring
setup_monitoring(project_root="C:\\MyProject")
```

## 📦 Publishing to PyPI (For Maintainers)

To make this available via `pip install`:

### 1. Update setup.py with correct details

```python
# Update email, version, etc.
```

### 2. Build distribution

```bash
python -m build
```

### 3. Upload to PyPI

```bash
python -m twine upload dist/*
```

### 4. Users can then install with:

```bash
pip install docker-mcp-server
```

## 🎯 Future: NPX-Style Installation

To enable `npx`-like installation for Python:

### Using pipx:

```bash
pipx install docker-mcp-server
docker-mcp-install --ide all
```

### Using uvx (modern alternative):

```bash
uvx docker-mcp-server
```

## 🐛 Troubleshooting

### Issue: "command not found" after install

**Solution:** Ensure Python Scripts directory is in PATH

```bash
# Windows
set PATH=%PATH%;%APPDATA%\Python\Python311\Scripts

# Linux/macOS
export PATH=$PATH:~/.local/bin
```

### Issue: Config file not found

**Solution:** Run with elevated permissions or specify path manually

```bash
python install.py --ide claude
# If fails, check the path printed and create directory
```

### Issue: Import errors

**Solution:** Reinstall dependencies

```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: IDE not detecting the MCP

**Solution:** 
1. Verify config file was updated (check the paths printed by installer)
2. Restart the IDE completely
3. Check IDE logs for MCP connection errors

## 📞 Support

If you encounter issues:

1. Check the installation logs
2. Verify config file paths
3. Test Python path: `which python` or `where python`
4. Open an issue on GitHub with:
   - OS and Python version
   - Installation command used
   - Error messages
   - Config file contents (sanitized)

## 🎉 Success Indicators

You'll know installation worked when:

- ✅ Installer prints "Installation complete!"
- ✅ Config files show docker-mcp entry
- ✅ IDE restart shows Docker MCP in available servers
- ✅ You can run MCP commands successfully
- ✅ All 20 tools are listed and functional

## 📚 Additional Resources

- [README.md](README.md) - Full documentation
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Smart workflow tutorial
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [GitHub Issues](https://github.com/Iswarya-Amzur/docker-mcp-python/issues) - Report bugs
