from __future__ import annotations

from playwright.async_api import Browser, async_playwright

_browser: Browser | None = None
_playwright_instance = None


async def _get_browser() -> Browser:
    global _browser, _playwright_instance
    if _browser is None:
        _playwright_instance = await async_playwright().start()
        _browser = await _playwright_instance.chromium.launch(headless=True)
    return _browser


async def scrape_page(url: str, timeout: int = 10000) -> str:
    try:
        browser = await _get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        text = await page.inner_text("body")
        await context.close()
        return text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {e}"


async def close_browser() -> None:
    global _browser, _playwright_instance
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None
