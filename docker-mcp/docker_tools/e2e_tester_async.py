"""
Async E2E Testing Module using Direct Playwright Library

This module provides browser automation testing using the Playwright Python library.
Uses Playwright's Async API for seamless integration with FastMCP's asyncio event loop.

Direct Playwright integration - no wrappers, no MCP layers, just pure Playwright.
Returns base64-encoded screenshots for display in chat.
"""

import subprocess
import os
import time
import logging
import json
import base64
import asyncio
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


async def check_containers_running_async(project_root: str) -> dict:
    """Check if docker-compose containers are running (async)."""
    try:
        process = await asyncio.create_subprocess_exec(
            "docker-compose", "ps", "-q",
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        container_ids = [cid for cid in stdout.decode().strip().split('\n') if cid]
        
        return {
            "running": len(container_ids) > 0,
            "count": len(container_ids),
            "container_ids": container_ids
        }
    except Exception as e:
        return {
            "running": False,
            "count": 0,
            "error": str(e)
        }


async def start_docker_compose_async(project_root: str, detached: bool = True) -> dict:
    """Start docker-compose stack (async)."""
    try:
        cmd = ["docker-compose", "up", "--build"]
        if detached:
            cmd.append("-d")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Docker Compose started successfully",
                    "output": stdout.decode('utf-8', errors='replace')
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start Docker Compose",
                    "error": stderr.decode('utf-8', errors='replace')
                }
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Docker Compose startup timeout (5 minutes)"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error starting Docker Compose: {str(e)}"
        }


async def wait_for_services_async(host: str = "localhost", backend_port: int = 8000,
                                   frontend_port: int = 3000, timeout: int = 60) -> dict:
    """Wait for services to be ready (async)."""
    import socket
    import asyncio
    
    start_time = time.time()
    services_ready = {"backend": False, "frontend": False}
    
    while time.time() - start_time < timeout:
        # Check backend
        if not services_ready["backend"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, backend_port))
                sock.close()
                if result == 0:
                    services_ready["backend"] = True
                    logger.info(f"Backend ready on port {backend_port}")
            except:
                pass
        
        # Check frontend
        if not services_ready["frontend"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, frontend_port))
                sock.close()
                if result == 0:
                    services_ready["frontend"] = True
                    logger.info(f"Frontend ready on port {frontend_port}")
            except:
                pass
        
        if services_ready["backend"] and services_ready["frontend"]:
            return {
                "status": "success",
                "message": "All services ready",
                "services": services_ready
            }
        
        await asyncio.sleep(2)
    
    return {
        "status": "partial" if any(services_ready.values()) else "error",
        "message": f"Services readiness timeout after {timeout}s",
        "services": services_ready
    }


async def screenshot_to_base64(page: Page, full_page: bool = True) -> str:
    """Capture screenshot and return as base64 data URL."""
    try:
        screenshot_bytes = await page.screenshot(full_page=full_page, type='png')
        base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_image}"
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return ""


async def _test_button_interactions_async(page: Page, results: dict):
    """Test clicking buttons (async)."""
    try:
        buttons = await page.locator("button, input[type='button'], input[type='submit']").all()
        
        if not buttons:
            results["interactions"].append("No buttons found")
            return
        
        clicked = 0
        for i, button in enumerate(buttons[:3]):
            try:
                if await button.is_visible():
                    button_text = await button.inner_text() or await button.get_attribute("value") or f"Button {i+1}"
                    logger.info(f"Clicking button: {button_text}")
                    await button.click(timeout=5000)
                    await page.wait_for_timeout(1000)
                    clicked += 1
                    results["interactions"].append(f"Clicked button: {button_text}")
            except Exception as e:
                logger.debug(f"Could not click button {i}: {e}")
        
        if clicked > 0:
            results["tests"].append({"name": "Button interactions", "status": "passed", "buttons_clicked": clicked})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Button interactions", "status": "skipped", "note": "No clickable buttons"})
    except Exception as e:
        results["tests"].append({"name": "Button interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_input_interactions_async(page: Page, results: dict):
    """Test filling input fields (async)."""
    try:
        inputs = await page.locator("input[type='text'], input[type='email'], input:not([type]), textarea").all()
        
        if not inputs:
            results["interactions"].append("No input fields found")
            return
        
        filled = 0
        test_data = {
            "text": "Test Task from E2E",
            "email": "test@example.com",
            "default": "Sample input"
        }
        
        for i, input_field in enumerate(inputs[:3]):
            try:
                if await input_field.is_visible() and not await input_field.is_disabled():
                    field_type = await input_field.get_attribute("type") or "default"
                    placeholder = await input_field.get_attribute("placeholder") or f"Field {i+1}"
                    
                    test_value = test_data.get(field_type, test_data["default"])
                    logger.info(f"Filling input: {placeholder} with '{test_value}'")
                    
                    await input_field.fill(test_value)
                    await page.wait_for_timeout(500)
                    filled += 1
                    results["interactions"].append(f"Filled field: {placeholder}")
            except Exception as e:
                logger.debug(f"Could not fill input {i}: {e}")
        
        if filled > 0:
            results["tests"].append({"name": "Input field interactions", "status": "passed", "fields_filled": filled})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Input field interactions", "status": "skipped", "note": "No fillable inputs"})
    except Exception as e:
        results["tests"].append({"name": "Input field interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_create_item_async(page: Page, results: dict, backend_url: str):
    """Test creating an item (async)."""
    try:
        created = False
        
        input_selectors = [
            "input[placeholder*='task' i]",
            "input[placeholder*='todo' i]",
            "input[placeholder*='add' i]",
            "input[type='text']:visible"
        ]
        
        for selector in input_selectors:
            try:
                input_field = page.locator(selector).first
                if await input_field.is_visible():
                    logger.info("Found input field, creating test item...")
                    await input_field.fill("E2E Test Task - Created by Playwright")
                    await page.wait_for_timeout(500)
                    
                    add_buttons = await page.locator("button:has-text('Add'), button:has-text('Create'), button:has-text('Submit'), button[type='submit']").all()
                    
                    for button in add_buttons:
                        if await button.is_visible():
                            logger.info("Clicking submit button...")
                            await button.click()
                            await page.wait_for_timeout(2000)
                            created = True
                            results["interactions"].append("Created new item via form")
                            break
                    
                    if created:
                        break
            except:
                continue
        
        if created:
            await page.wait_for_timeout(1000)
            results["tests"].append({"name": "Create item interaction", "status": "passed", "action": "Item created"})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Create item interaction", "status": "skipped", "note": "No create form found"})
    except Exception as e:
        results["tests"].append({"name": "Create item interaction", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_navigation_async(page: Page, results: dict):
    """Test navigation (async)."""
    try:
        links = await page.locator("a[href], button:has-text('Home'), button:has-text('About')").all()
        
        navigated = 0
        for i, link in enumerate(links[:3]):
            try:
                if await link.is_visible():
                    link_text = await link.inner_text() or await link.get_attribute("href") or f"Link {i+1}"
                    href = await link.get_attribute("href")
                    
                    if href and (href.startswith("http://") or href.startswith("https://")) and "localhost" not in href:
                        continue
                    
                    logger.info(f"Navigating to: {link_text}")
                    await link.click(timeout=5000)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(1000)
                    navigated += 1
                    results["interactions"].append(f"Navigated to: {link_text}")
                    
                    await page.go_back()
                    await page.wait_for_timeout(500)
            except Exception as e:
                logger.debug(f"Could not navigate via link {i}: {e}")
        
        if navigated > 0:
            results["tests"].append({"name": "Navigation interactions", "status": "passed", "links_tested": navigated})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Navigation interactions", "status": "skipped", "note": "No navigation links"})
    except Exception as e:
        results["tests"].append({"name": "Navigation interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_form_submission_async(page: Page, results: dict):
    """Test form submission (async)."""
    try:
        forms = await page.locator("form").all()
        
        if not forms:
            results["interactions"].append("No forms found")
            return
        
        submitted = 0
        for i, form in enumerate(forms[:2]):
            try:
                if await form.is_visible():
                    inputs = await form.locator("input[type='text'], input:not([type]), textarea").all()
                    
                    for input_field in inputs:
                        if await input_field.is_visible() and not await input_field.is_disabled():
                            await input_field.fill("Test data from E2E")
                            await page.wait_for_timeout(300)
                    
                    submit = form.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").first
                    
                    if await submit.is_visible():
                        logger.info(f"Submitting form {i+1}")
                        await submit.click()
                        await page.wait_for_timeout(2000)
                        submitted += 1
                        results["interactions"].append(f"Submitted form {i+1}")
            except Exception as e:
                logger.debug(f"Could not submit form {i}: {e}")
        
        if submitted > 0:
            results["tests"].append({"name": "Form submission", "status": "passed", "forms_submitted": submitted})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Form submission", "status": "skipped", "note": "No submittable forms"})
    except Exception as e:
        results["tests"].append({"name": "Form submission", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def run_interactive_tests_async(
    project_root: str,
    frontend_url: str = "http://localhost:3000",
    backend_url: str = "http://localhost:3000",
    headless: bool = False,
    perform_interactions: bool = True
) -> dict:
    """
    Run browser automation tests using direct Playwright library (Async API).
    
    Pure Playwright integration - uses playwright.async_api directly.
    Returns base64-encoded screenshots.
    
    Args:
        project_root: Root directory
        frontend_url: Frontend URL
        backend_url: Backend URL
        headless: Run in headless mode
        perform_interactions: Perform user interactions
        
    Returns:
        Dict with test results and base64 screenshots
    """
    import asyncio
    
    results = {
        "tests": [],
        "passed": 0,
        "failed": 0,
        "total": 0,
        "interactions": [],
        "screenshot_initial": "",
        "screenshot_after": ""
    }
    
    try:
        async with async_playwright() as p:
            logger.info(f"🌐 Launching {'headless' if headless else 'VISIBLE'} Chromium browser...")
            
            browser = await p.chromium.launch(
                headless=headless,
                slow_mo=500 if not headless else 0,
                args=['--start-maximized'] if not headless else []
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                no_viewport=True if not headless else False
            )
            
            page = await context.new_page()
            logger.info("✅ Browser opened!")
            
            # Test 1: Backend health check
            results["total"] += 1
            try:
                response = await page.request.get(f"{backend_url}/health")
                if response.ok:
                    results["tests"].append({"name": "Backend health check", "status": "passed"})
                    results["passed"] += 1
                else:
                    results["tests"].append({"name": "Backend health check", "status": "failed", "error": f"Status {response.status}"})
                    results["failed"] += 1
            except Exception as e:
                results["tests"].append({"name": "Backend health check", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # Test 2: Frontend loads
            results["total"] += 1
            try:
                logger.info(f"🌐 Loading frontend at {frontend_url}")
                await page.goto(frontend_url, wait_until="networkidle", timeout=30000)
                title = await page.title()
                
                logger.info(f"✅ Page loaded: {title}")
                results["tests"].append({"name": "Frontend loads successfully", "status": "passed", "title": title})
                results["passed"] += 1
                
                # Capture initial screenshot as base64
                results["screenshot_initial"] = await screenshot_to_base64(page, full_page=True)
                
            except Exception as e:
                results["tests"].append({"name": "Frontend loads successfully", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # Test 3: API calls
            results["total"] += 1
            try:
                api_calls = []
                page.on("request", lambda request: api_calls.append(request.url) if backend_url in request.url else None)
                
                await page.reload(wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                if api_calls:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "passed", "api_calls": len(api_calls)})
                    results["passed"] += 1
                else:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "warning", "note": "No API calls detected"})
            except Exception as e:
                results["tests"].append({"name": "Frontend-Backend communication", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # Perform interactions
            if perform_interactions:
                logger.info("Starting interactive tests...")
                
                interaction_tests = [
                    ("Find and click buttons", lambda: _test_button_interactions_async(page, results)),
                    ("Fill input fields", lambda: _test_input_interactions_async(page, results)),
                    ("Create/Add items", lambda: _test_create_item_async(page, results, backend_url)),
                    ("Navigate routes", lambda: _test_navigation_async(page, results)),
                    ("Test form submissions", lambda: _test_form_submission_async(page, results))
                ]
                
                for test_name, test_func in interaction_tests:
                    results["total"] += 1
                    try:
                        await test_func()
                    except Exception as e:
                        logger.warning(f"Interaction test '{test_name}' failed: {e}")
                
                # Capture final screenshot as base64
                results["screenshot_after"] = await screenshot_to_base64(page, full_page=True)
                
                if not headless:
                    logger.info("Tests completed! Keeping browser open for 15s...")
                    await page.wait_for_timeout(15000)
            
            await browser.close()
        
        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results
        
    except Exception as e:
        logger.error(f"Error during async tests: {e}")
        return {
            "status": "error",
            "message": f"Error running interactive tests: {str(e)}",
            "tests": [],
            "passed": 0,
            "failed": 1,
            "total": 1
        }


async def launch_and_test_async(
    project_root: str,
    backend_port: int = 8000,
    frontend_port: int = 3000,
    cleanup: bool = False,
    headless: bool = False,
    show_browser: bool = True
) -> dict:
    """
    Complete async workflow: check containers, start if needed, run tests.
    Returns dict with base64 screenshots.
    """
    import asyncio
    
    result = {
        "status": "success",
        "steps": [],
        "tests": [],
        "screenshots": {}
    }
    
    # Step 1: Check containers
    result["steps"].append({"name": "Check containers", "status": "running"})
    container_check = await check_containers_running_async(project_root)
    
    if not container_check.get("running", False):
        result["steps"].append({"name": "Start containers", "status": "running"})
        start_result = await start_docker_compose_async(project_root, detached=True)
        
        if start_result["status"] != "success":
            result["status"] = "error"
            result["error"] = start_result.get("message", "Failed to start containers")
            return result
        
        result["steps"][-1]["status"] = "success"
    else:
        result["steps"].append({"name": "Containers already running", "status": "success"})
    
    # Step 2: Wait for services
    result["steps"].append({"name": "Wait for services", "status": "running"})
    wait_result = await wait_for_services_async("localhost", backend_port, frontend_port, timeout=60)
    
    if wait_result["status"] == "error":
        result["status"] = "error"
        result["error"] = wait_result.get("message", "Services not ready")
        return result
    
    result["steps"][-1]["status"] = "success"
    
    # Step 3: Run interactive tests
    if show_browser:
        result["steps"].append({"name": "Run E2E tests", "status": "running"})
        
        frontend_url = f"http://localhost:{frontend_port}"
        backend_url = f"http://localhost:{backend_port}"
        
        test_results = await run_interactive_tests_async(
            project_root,
            frontend_url,
            backend_url,
            headless=headless,
            perform_interactions=True
        )
        
        result["steps"][-1]["status"] = test_results.get("status", "success")
        result["tests"] = test_results.get("tests", [])
        result["interactions"] = test_results.get("interactions", [])
        result["screenshots"]["initial"] = test_results.get("screenshot_initial", "")
        result["screenshots"]["after"] = test_results.get("screenshot_after", "")
        result["test_summary"] = {
            "passed": test_results.get("passed", 0),
            "failed": test_results.get("failed", 0),
            "total": test_results.get("total", 0)
        }
    
    return result
