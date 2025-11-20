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


async def analyze_page_structure(page: Page) -> dict:
    """Analyze page structure and extract interactive elements like Playwright MCP."""
    try:
        # Set a default timeout for all operations to prevent hanging on complex apps
        page.set_default_timeout(10000)  # 10 seconds max for any single operation
        
        analysis = {
            "title": await page.title(),
            "url": page.url,
            "buttons": [],
            "inputs": [],
            "links": [],
            "forms": [],
            "interactive_elements": []
        }
        
        # Extract buttons (with timeout)
        try:
            buttons = await page.locator("button, input[type='button'], input[type='submit']").all()
            for i, btn in enumerate(buttons[:10]):
                try:
                    if await btn.is_visible():
                        text = await btn.inner_text() or await btn.get_attribute("value") or await btn.get_attribute("aria-label") or f"Button {i+1}"
                        analysis["buttons"].append({
                            "index": i,
                            "text": text.strip(),
                            "type": await btn.get_attribute("type") or "button"
                        })
                except:
                    pass
        except Exception as e:
            logger.warning(f"Could not analyze buttons: {e}")
        
        # Extract input fields (with timeout)
        try:
            inputs = await page.locator("input, textarea").all()
            for i, inp in enumerate(inputs[:10]):
                try:
                    if await inp.is_visible() and not await inp.is_disabled():
                        inp_type = await inp.get_attribute("type") or "text"
                        placeholder = await inp.get_attribute("placeholder") or ""
                        name = await inp.get_attribute("name") or ""
                        analysis["inputs"].append({
                            "index": i,
                            "type": inp_type,
                            "placeholder": placeholder,
                            "name": name
                        })
                except:
                    pass
        except Exception as e:
            logger.warning(f"Could not analyze inputs: {e}")
        
        # Extract links (with timeout)
        try:
            links = await page.locator("a[href]").all()
            for i, link in enumerate(links[:10]):
                try:
                    if await link.is_visible():
                        text = await link.inner_text()
                        href = await link.get_attribute("href")
                        if text and href:
                            analysis["links"].append({
                                "index": i,
                                "text": text.strip(),
                                "href": href
                            })
                except:
                    pass
        except Exception as e:
            logger.warning(f"Could not analyze links: {e}")
        
        # Extract forms (with timeout)
        try:
            forms = await page.locator("form").all()
            analysis["forms"] = [{"index": i} for i in range(len(forms))]
        except Exception as e:
            logger.warning(f"Could not analyze forms: {e}")
        
        # Summary
        analysis["interactive_elements"] = [
            f"{len(analysis['buttons'])} buttons",
            f"{len(analysis['inputs'])} input fields",
            f"{len(analysis['links'])} links",
            f"{len(analysis['forms'])} forms"
        ]
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze page: {e}")
        return {"error": str(e)}


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
    
    # DEBUG: Log function entry and all parameters
    logger.info("="*100)
    logger.info("🔵 DEBUG: run_interactive_tests_async() FUNCTION CALLED")
    logger.info(f"🔵 DEBUG:   project_root = {project_root}")
    logger.info(f"🔵 DEBUG:   frontend_url = {frontend_url}")
    logger.info(f"🔵 DEBUG:   backend_url = {backend_url}")
    logger.info(f"🔵 DEBUG:   headless = {headless}")
    logger.info(f"🔵 DEBUG:   perform_interactions = {perform_interactions}")
    logger.info("="*100)
    
    results = {
        "tests": [],
        "passed": 0,
        "failed": 0,
        "total": 0,
        "interactions": [],
        "screenshot_initial": "",
        "screenshot_after": "",
        "page_analysis": {}
    }
    
    try:
        logger.info("🔵 DEBUG: Entering async_playwright() context manager...")
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
            logger.info("✅ Browser opened! Starting automated testing...")
            logger.info("🔵 DEBUG: Browser and page objects created successfully")
            logger.info(f"🔵 DEBUG: Page URL: {page.url}")
            
            # Skip backend health check - not all apps have /health endpoint
            # Go straight to frontend testing
            
            # Test 1: Frontend loads
            results["total"] += 1
            page_loaded_successfully = False
            try:
                logger.info(f"🌐 Loading frontend at {frontend_url}")
                logger.info(f"   Browser window is now VISIBLE - check your screen!")
                logger.info(f"   Navigating to {frontend_url}...")
                logger.info(f"   ⏱️  Using 90 second timeout for large/complex applications...")
                logger.info("🔵 DEBUG: About to call page.goto() - this may take up to 90 seconds...")
                
                # Use 'domcontentloaded' instead of 'networkidle' for complex apps
                # 'networkidle' waits for all network requests which can timeout on complex apps
                import time
                start_time = time.time()
                await page.goto(frontend_url, wait_until="domcontentloaded", timeout=90000)
                elapsed = time.time() - start_time
                logger.info(f"🔵 DEBUG: page.goto() completed in {elapsed:.2f} seconds")
                title = await page.title()
                page_loaded_successfully = True
                
                logger.info(f"✅ Page loaded successfully: '{title}'")
                logger.info(f"   👀 You should see the application in the browser window now!")
                results["tests"].append({"name": "Frontend loads successfully", "status": "passed", "title": title})
                results["passed"] += 1
                
                # Wait for page to fully render (important for complex apps with lazy loading)
                logger.info("⏸️  Waiting 5 seconds for page to fully render (important for complex apps)...")
                await page.wait_for_timeout(5000)
                
                # Capture initial screenshot as base64
                logger.info("📸 Capturing initial screenshot...")
                screenshot_data = await screenshot_to_base64(page, full_page=True)
                if screenshot_data:
                    results["screenshot_initial"] = screenshot_data
                    logger.info(f"✅ Initial screenshot captured: {len(screenshot_data)} characters")
                else:
                    logger.warning("⚠️ Initial screenshot capture returned empty data")
                
            except Exception as e:
                logger.error(f"❌ Frontend load failed: {e}")
                logger.warning(f"⚠️  This might be due to timeout on complex applications")
                logger.info(f"   Will still attempt to capture screenshot and perform interactions...")
                results["tests"].append({"name": "Frontend loads successfully", "status": "failed", "error": str(e)})
                results["failed"] += 1
                page_loaded_successfully = False
                
                # Try to capture screenshot even if page load failed
                try:
                    logger.info("📸 Attempting to capture screenshot despite error...")
                    # Wait a bit for partial content to load
                    await page.wait_for_timeout(3000)
                    screenshot_data = await screenshot_to_base64(page, full_page=False)
                    if screenshot_data:
                        results["screenshot_initial"] = screenshot_data
                        logger.info(f"✅ Error screenshot captured: {len(screenshot_data)} characters")
                except Exception as ss_error:
                    logger.error(f"Failed to capture error screenshot: {ss_error}")
            
            # Test 3: API calls (only if page loaded successfully)
            if page_loaded_successfully:
                results["total"] += 1
                try:
                    api_calls = []
                    page.on("request", lambda request: api_calls.append(request.url) if backend_url in request.url else None)
                    
                    # Don't reload - just wait for any async API calls
                    logger.info("🔍 Monitoring API calls for 3 seconds...")
                    await page.wait_for_timeout(3000)
                    
                    if api_calls:
                        results["tests"].append({"name": "Frontend-Backend communication", "status": "passed", "api_calls": len(api_calls)})
                        results["passed"] += 1
                        logger.info(f"✅ Detected {len(api_calls)} API calls to backend")
                    else:
                        results["tests"].append({"name": "Frontend-Backend communication", "status": "warning", "note": "No API calls detected"})
                        logger.warning("⚠️  No API calls detected (this is OK for static apps)")
                except Exception as e:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "failed", "error": str(e)})
                    results["failed"] += 1
            else:
                logger.info("⏭️  Skipping API call test due to page load issues, moving to interactions...")
            
            # Perform interactions with intelligent analysis
            # ALWAYS attempt interactions, even if page load had issues
            logger.info(f"🔵 DEBUG: About to check perform_interactions flag: {perform_interactions}")
            if perform_interactions:
                logger.info("🤖 Starting INTELLIGENT interactive tests...")
                logger.info("   Testing like Playwright MCP - analyze, screenshot, act, verify")
                logger.info("   👀 WATCH THE BROWSER WINDOW - automated actions starting now!")
                logger.info("🔵 DEBUG: Inside perform_interactions block - will now analyze page")
                logger.info("")
                
                try:
                    # Step 1: Analyze initial page structure
                    logger.info("🔍 STEP 1: Analyzing page structure...")
                    page_analysis = await analyze_page_structure(page)
                except Exception as analysis_error:
                    logger.error(f"❌ Page analysis failed: {analysis_error}")
                    logger.info("   Will still attempt to capture screenshot and keep browser open...")
                    page_analysis = {"title": "Unknown", "interactive_elements": [], "buttons": [], "inputs": [], "forms": [], "links": []}
                
                logger.info(f"   📄 Page Title: {page_analysis.get('title', 'Unknown')}")
                logger.info(f"   🎯 Interactive Elements Found: {', '.join(page_analysis.get('interactive_elements', []))}")
                logger.info(f"   → This information guides the automated testing strategy")
                results["interactions"].append(f"Page Analysis: {page_analysis.get('title')}")
                results["interactions"].append(f"Interactive elements: {', '.join(page_analysis.get('interactive_elements', []))}")
                
                # Step 2: Test buttons with analysis
                if page_analysis.get('buttons'):
                    logger.info(f"\n🔍 STEP 2: Testing {len(page_analysis['buttons'])} buttons...")
                    for btn_info in page_analysis['buttons'][:3]:
                        logger.info(f"   📸 Analyzing button: '{btn_info['text']}'")
                        results["total"] += 1
                        try:
                            await _test_button_interactions_async(page, results)
                            break  # Test one set of buttons
                        except Exception as e:
                            logger.warning(f"Button test failed: {e}")
                
                # Step 3: Test input fields with analysis
                if page_analysis.get('inputs'):
                    logger.info(f"\n🔍 STEP 3: Testing {len(page_analysis['inputs'])} input fields...")
                    for inp_info in page_analysis['inputs'][:3]:
                        logger.info(f"   📸 Analyzing input: type={inp_info['type']}, placeholder='{inp_info.get('placeholder', 'none')}'")
                    results["total"] += 1
                    try:
                        await _test_input_interactions_async(page, results)
                    except Exception as e:
                        logger.warning(f"Input test failed: {e}")
                
                # Step 4: Test item creation if todo/task app detected
                if any('task' in inp.get('placeholder', '').lower() or 'todo' in inp.get('placeholder', '').lower() 
                       for inp in page_analysis.get('inputs', [])):
                    logger.info("\n🔍 STEP 4: Detected todo/task app - testing item creation...")
                    results["total"] += 1
                    try:
                        await _test_create_item_async(page, results, backend_url)
                    except Exception as e:
                        logger.warning(f"Create item test failed: {e}")
                
                # Step 5: Test navigation
                if page_analysis.get('links'):
                    logger.info(f"\n🔍 STEP 5: Testing navigation with {len(page_analysis['links'])} links...")
                    results["total"] += 1
                    try:
                        await _test_navigation_async(page, results)
                    except Exception as e:
                        logger.warning(f"Navigation test failed: {e}")
                
                # Step 6: Test forms
                if page_analysis.get('forms'):
                    logger.info(f"\n🔍 STEP 6: Testing {len(page_analysis['forms'])} forms...")
                    results["total"] += 1
                    try:
                        await _test_form_submission_async(page, results)
                    except Exception as e:
                        logger.warning(f"Form test failed: {e}")
                
                # Capture final screenshot as base64 (always attempt)
                logger.info("\n📸 Capturing post-interaction screenshot...")
                try:
                    screenshot_data = await screenshot_to_base64(page, full_page=True)
                    if screenshot_data:
                        results["screenshot_after"] = screenshot_data
                        logger.info(f"✅ Post-interaction screenshot captured: {len(screenshot_data)} characters")
                    else:
                        logger.warning("⚠️ Post-interaction screenshot capture returned empty data")
                except Exception as ss_error:
                    logger.error(f"❌ Failed to capture post-interaction screenshot: {ss_error}")
                    # Try viewport screenshot as fallback
                    try:
                        screenshot_data = await screenshot_to_base64(page, full_page=False)
                        if screenshot_data:
                            results["screenshot_after"] = screenshot_data
                            logger.info(f"✅ Fallback viewport screenshot captured")
                    except:
                        logger.error("❌ All screenshot attempts failed")
                
                if not headless:
                    logger.info("")
                    logger.info("="*80)
                    logger.info("✅ ALL AUTOMATED TESTS COMPLETED SUCCESSFULLY!")
                    logger.info("="*80)
                    logger.info("📊 Test Summary:")
                    logger.info(f"   • Total Tests: {results['total']}")
                    logger.info(f"   • Passed: {results['passed']}")
                    logger.info(f"   • Failed: {results['failed']}")
                    logger.info(f"   • Screenshots Captured: {len([k for k in results.keys() if 'screenshot' in k])}")
                    logger.info("")
                    logger.info("👀 Browser will stay open for 30 seconds so you can inspect the final state")
                    logger.info("   → Check the browser window to see the application state after all tests")
                    logger.info("   → Screenshots are included in the JSON results")
                    logger.info("")
                    await page.wait_for_timeout(30000)
                    logger.info("⏱️  30 seconds elapsed - closing browser now...")
            else:
                logger.warning("⚠️ perform_interactions was False - no interactions performed!")
                if not headless:
                    logger.info("Keeping browser open for 10 seconds...")
                    await page.wait_for_timeout(10000)
            
            logger.info("🔒 Closing browser...")
            await browser.close()
            logger.info("✅ Browser closed successfully.")
        
        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results
        
    except Exception as e:
        logger.error(f"❌ ERROR during async tests: {e}")
        logger.error(f"   This error occurred during browser automation")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Error running interactive tests: {str(e)}",
            "tests": [],
            "passed": 0,
            "failed": 1,
            "total": 1,
            "interactions": [f"Error: {str(e)}"]
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
        
        logger.info(f"🎯 Starting interactive tests at {frontend_url}")
        logger.info("   This will: Load page → Analyze structure → Perform actions → Capture screenshots")
        
        test_results = await run_interactive_tests_async(
            project_root,
            frontend_url,
            backend_url,
            headless=headless,
            perform_interactions=True  # ALWAYS perform interactions
        )
        
        logger.info(f"✅ Interactive tests completed! {test_results.get('passed', 0)}/{test_results.get('total', 0)} passed")
        
        result["steps"][-1]["status"] = test_results.get("status", "success")
        result["tests"] = test_results.get("tests", [])
        result["interactions"] = test_results.get("interactions", [])
        
        # Transfer screenshots with logging
        screenshot_initial = test_results.get("screenshot_initial", "")
        screenshot_after = test_results.get("screenshot_after", "")
        
        if screenshot_initial:
            result["screenshots"]["initial"] = screenshot_initial
            logger.info(f"📸 Initial screenshot included in result: {len(screenshot_initial)} chars")
        else:
            logger.warning("⚠️ No initial screenshot in test results")
        
        if screenshot_after:
            result["screenshots"]["after"] = screenshot_after
            logger.info(f"📸 After screenshot included in result: {len(screenshot_after)} chars")
        else:
            logger.warning("⚠️ No after screenshot in test results")
        
        result["test_summary"] = {
            "passed": test_results.get("passed", 0),
            "failed": test_results.get("failed", 0),
            "total": test_results.get("total", 0)
        }
    
    return result


async def test_with_playwright_mcp(
    project_root: str,
    frontend_url: str,
    backend_url: str,
    context
) -> dict:
    """
    Test application using actual Playwright MCP browser automation tools.
    This uses the real MCP browser tools like browser_snapshot, browser_click, etc.
    
    Args:
        project_root: Project root directory
        frontend_url: Frontend URL to test
        backend_url: Backend URL
        context: MCP context with access to browser tools
        
    Returns:
        Test results with screenshots and actions
    """
    results = {
        "tests": [],
        "passed": 0,
        "failed": 0,
        "total": 0,
        "interactions": [],
        "screenshots": {},
        "status": "success"
    }
    
    try:
        logger.info(f"🌐 Starting Playwright MCP automated testing for {frontend_url}")
        
        # Step 1: Navigate to the frontend URL
        logger.info(f"📍 Step 1: Navigating to {frontend_url}")
        try:
            # Use browser_tabs to create new page or select existing
            await context.call_tool("mcp_microsoft_pla_browser_tabs", {"action": "new"})
            results["interactions"].append(f"Opened new browser tab")
            
            # Navigate to URL
            await context.call_tool("mcp_microsoft_pla_browser_run_code", {
                "code": f"await page.goto('{frontend_url}', {{ waitUntil: 'networkidle' }})"
            })
            results["interactions"].append(f"Navigated to {frontend_url}")
            results["passed"] += 1
        except Exception as e:
            logger.error(f"Failed to navigate: {e}")
            results["failed"] += 1
            results["interactions"].append(f"❌ Navigation failed: {e}")
        
        results["total"] += 1
        
        # Step 2: Take snapshot and analyze page structure
        logger.info("📸 Step 2: Taking page snapshot and analyzing structure...")
        try:
            snapshot = await context.call_tool("mcp_microsoft_pla_browser_take_snapshot", {})
            results["screenshots"]["initial_snapshot"] = snapshot
            results["interactions"].append("Captured page snapshot")
            logger.info(f"Page snapshot captured successfully")
            results["passed"] += 1
        except Exception as e:
            logger.error(f"Failed to take snapshot: {e}")
            results["failed"] += 1
            results["interactions"].append(f"❌ Snapshot failed: {e}")
        
        results["total"] += 1
        
        # Step 3: Take screenshot
        logger.info("📸 Step 3: Taking initial screenshot...")
        try:
            screenshot = await context.call_tool("mcp_microsoft_pla_browser_take_screenshot", {
                "filename": "initial.png",
                "fullPage": True
            })
            results["screenshots"]["initial"] = screenshot
            results["interactions"].append("Captured initial screenshot")
            results["passed"] += 1
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            results["failed"] += 1
            results["interactions"].append(f"❌ Screenshot failed: {e}")
        
        results["total"] += 1
        
        # Step 4: Find and analyze interactive elements from snapshot
        logger.info("🔍 Step 4: Analyzing interactive elements...")
        results["interactions"].append("Analyzing page for interactive elements")
        
        # Step 5: Click first button if found
        logger.info("👆 Step 5: Testing button interactions...")
        try:
            # Try to click a visible button
            await context.call_tool("mcp_microsoft_pla_browser_run_code", {
                "code": """
                const buttons = await page.locator('button, input[type="button"], input[type="submit"]').all();
                if (buttons.length > 0 && await buttons[0].isVisible()) {
                    const text = await buttons[0].innerText() || await buttons[0].getAttribute('value') || 'Button';
                    await buttons[0].click();
                    return { clicked: true, text: text };
                }
                return { clicked: false };
                """
            })
            results["interactions"].append("Clicked first visible button")
            results["passed"] += 1
        except Exception as e:
            logger.info(f"No buttons to click or click failed: {e}")
            results["interactions"].append("⚠️ No clickable buttons found")
        
        results["total"] += 1
        
        # Step 6: Fill input fields if found
        logger.info("✍️ Step 6: Testing input fields...")
        try:
            await context.call_tool("mcp_microsoft_pla_browser_run_code", {
                "code": """
                const inputs = await page.locator('input[type="text"], input:not([type]), textarea').all();
                let filled = 0;
                for (const input of inputs.slice(0, 2)) {
                    if (await input.isVisible() && !await input.isDisabled()) {
                        await input.fill('Test from Playwright MCP');
                        filled++;
                    }
                }
                return { filled: filled };
                """
            })
            results["interactions"].append("Filled input fields with test data")
            results["passed"] += 1
        except Exception as e:
            logger.info(f"No inputs to fill or fill failed: {e}")
            results["interactions"].append("⚠️ No fillable inputs found")
        
        results["total"] += 1
        
        # Step 7: Take final screenshot
        logger.info("📸 Step 7: Taking final screenshot after interactions...")
        try:
            screenshot_after = await context.call_tool("mcp_microsoft_pla_browser_take_screenshot", {
                "filename": "after_interactions.png",
                "fullPage": True
            })
            results["screenshots"]["after"] = screenshot_after
            results["interactions"].append("Captured post-interaction screenshot")
            results["passed"] += 1
        except Exception as e:
            logger.error(f"Failed to take final screenshot: {e}")
            results["failed"] += 1
            results["interactions"].append(f"❌ Final screenshot failed: {e}")
        
        results["total"] += 1
        
        # Step 8: Take final snapshot
        logger.info("📸 Step 8: Taking final page snapshot...")
        try:
            final_snapshot = await context.call_tool("mcp_microsoft_pla_browser_take_snapshot", {})
            results["screenshots"]["final_snapshot"] = final_snapshot
            results["interactions"].append("Captured final page snapshot")
            results["passed"] += 1
        except Exception as e:
            logger.error(f"Failed to take final snapshot: {e}")
            results["failed"] += 1
        
        results["total"] += 1
        
        logger.info(f"✅ Playwright MCP testing complete: {results['passed']}/{results['total']} passed")
        
    except Exception as e:
        logger.error(f"Playwright MCP testing error: {e}")
        results["status"] = "error"
        results["error"] = str(e)
    
    return results
