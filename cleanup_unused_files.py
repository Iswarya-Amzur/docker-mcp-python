"""
Script to remove unused files from docker-mcp codebase
Run this to clean up test files, backups, and unused modules
"""

import os
import shutil

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_MCP_DIR = os.path.join(BASE_DIR, "docker-mcp")

# Files to remove
FILES_TO_REMOVE = [
    # Backup/Old server files
    "docker-mcp/server_backup_20tools.py",
    "docker-mcp/server_streamlined.py",
    "docker-mcp/debug_services.py",
    
    # Root test files
    "test_auto_fix_health.py",
    "test_debug_e2e.py",
    "test_language_detection.py",
    "test_root_language_priority.py",
    "test_service_detection.py",
    "test_user_issue_scenario.py",
    
    # Docker-mcp test files
    "docker-mcp/test_autofix.py",
    "docker-mcp/test_dockerfile_simple.py",
    "docker-mcp/test_dockerization.py",
    "docker-mcp/test_e2e_workflow.py",
    "docker-mcp/test_fixed_generation.py",
    "docker-mcp/test_port_detection.py",
    "docker-mcp/test_screenshot_fix.py",
    
    # Unused tool files
    "docker-mcp/docker_tools/analyzer_enhanced.py",
    "docker-mcp/docker_tools/multi_service_handler_enhanced.py",
    "docker-mcp/docker_tools/e2e_tester.py",
    "docker-mcp/docker_tools/comprehensive_workflow.py",
    
    # Temporary/fix documentation
    "COMPLEX_APP_FIX.md",
    "DEBUG_ACTION_PLAN.md",
    "SERVICE_DETECTION_FIX.md",
    "docker-mcp/CLEANUP_AND_REBUILD_GUIDE.md",
    "docker-mcp/ENHANCEMENTS.md",
]

# Documentation files that can be consolidated/removed (optional)
OPTIONAL_DOCS_TO_REMOVE = [
    "docker-mcp/docs/DOCKERIZATION_FLOW_FIX.md",
    "docker-mcp/docs/FIX_SUMMARY.md",
    "docker-mcp/docs/GRAFANA_FIX_SUMMARY.md",
    "docker-mcp/docs/GRAFANA_FIXES.md",
    "docker-mcp/docs/IMPLEMENTATION_SUMMARY.md",
    "docker-mcp/docs/SCREENSHOT_DISPLAY_FIX.md",
    "docker-mcp/docs/TOOL_CONSOLIDATION.md",
    "docker-mcp/docs/BEFORE_AFTER_COMPARISON.md",
    "docker-mcp/docs/AUTO_FIX_IMPLEMENTATION.md",
    "docker-mcp/docs/AUTO_FIX_GUIDE.md",
]

def remove_files(file_list, dry_run=True):
    """Remove files from the list"""
    removed = []
    not_found = []
    errors = []
    
    for file_path in file_list:
        full_path = os.path.join(BASE_DIR, file_path)
        
        if os.path.exists(full_path):
            try:
                if dry_run:
                    print(f"[DRY RUN] Would remove: {file_path}")
                    removed.append(file_path)
                else:
                    os.remove(full_path)
                    print(f"✅ Removed: {file_path}")
                    removed.append(file_path)
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
                errors.append((file_path, str(e)))
        else:
            not_found.append(file_path)
    
    return removed, not_found, errors

def main():
    """Main cleanup function"""
    print("=" * 80)
    print("Docker MCP Codebase Cleanup")
    print("=" * 80)
    print()
    
    # Ask user for confirmation
    print("This script will remove the following types of files:")
    print("  - Backup server files (server_backup_20tools.py, server_streamlined.py)")
    print("  - Test files (test_*.py)")
    print("  - Unused tool modules (analyzer_enhanced.py, etc.)")
    print("  - Temporary documentation files")
    print()
    
    response = input("Do you want to see what would be removed? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    print("\n" + "=" * 80)
    print("DRY RUN - Files that would be removed:")
    print("=" * 80)
    removed, not_found, errors = remove_files(FILES_TO_REMOVE, dry_run=True)
    
    if not_found:
        print(f"\n⚠️  Files not found (already removed?): {len(not_found)}")
        for f in not_found[:5]:  # Show first 5
            print(f"  - {f}")
        if len(not_found) > 5:
            print(f"  ... and {len(not_found) - 5} more")
    
    print(f"\n📊 Summary: {len(removed)} files would be removed")
    
    print("\n" + "=" * 80)
    response = input("\nProceed with actual removal? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Cancelled.")
        return
    
    print("\n" + "=" * 80)
    print("REMOVING FILES...")
    print("=" * 80)
    removed, not_found, errors = remove_files(FILES_TO_REMOVE, dry_run=False)
    
    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"✅ Removed: {len(removed)} files")
    if errors:
        print(f"❌ Errors: {len(errors)} files")
        for f, err in errors:
            print(f"  - {f}: {err}")
    
    # Optional docs removal
    print("\n" + "=" * 80)
    print("OPTIONAL: Remove fix/implementation documentation?")
    print("=" * 80)
    print(f"This will remove {len(OPTIONAL_DOCS_TO_REMOVE)} documentation files")
    print("These are historical fix/implementation notes that may not be needed.")
    response = input("\nRemove optional docs? (yes/no): ").strip().lower()
    
    if response == 'yes':
        removed_docs, _, errors_docs = remove_files(OPTIONAL_DOCS_TO_REMOVE, dry_run=False)
        print(f"\n✅ Removed {len(removed_docs)} documentation files")
        if errors_docs:
            print(f"❌ Errors: {len(errors_docs)} files")
    
    print("\n✨ Codebase cleanup complete!")
    print("You may want to run: git status")

if __name__ == "__main__":
    main()
