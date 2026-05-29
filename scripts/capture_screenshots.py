"""Capture reproducible public-demo screenshots in synthetic data mode."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, TimeoutError, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 1000

SCREENSHOT_PAGES = (
    ("Overview", "/", "01_overview.png", 0),
    ("Comparables", "/_comparables_page", "02_comparables.png", 1),
    ("Analysis", "/_analysis_page", "03_analysis.png", 4),
    ("Report", "/_report_page", "04_report.png", 0),
    ("About", "/_about_page", "05_about.png", 0),
)

PRIVATE_COMPARABLE_NAME_TOKENS = (
    "PHARMAAND",
    "PHARMORE",
    "BB FARMA",
    "TEDIS",
    "MICERIUM",
    "ALCYON",
    "UFM - UNIONE",
    "SAIMA",
    "CLUB SALUTE",
    "AMEFA",
    "VYGON",
    "DOCMORRIS",
    "OPELLA",
    "INTERCOS",
    "MUNDIPHARMA",
)


def main() -> None:
    """Launch the app in synthetic mode and capture all public screenshots."""

    _reset_synthetic_decisions()
    port = _find_free_port()
    base_url = f"http://localhost:{port}"
    process = _start_streamlit(port)

    try:
        _wait_for_server(base_url, process)
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            _capture_pages(base_url, temp_dir)
            _replace_screenshots(temp_dir)
    finally:
        _stop_process(process)

    print(f"Saved synthetic screenshots to {SCREENSHOTS_DIR}")


def _reset_synthetic_decisions() -> None:
    """Reset mutable synthetic decisions so local edits cannot affect screenshots."""

    os.environ["APP_DATA_MODE"] = "synthetic"
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from src import config
    from src.comparables import reset_to_defaults

    reset_to_defaults(data_mode=config.DATA_MODE_SYNTHETIC)


def _find_free_port() -> int:
    """Return an available localhost port."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_streamlit(port: int) -> subprocess.Popen[str]:
    """Start Streamlit in synthetic mode on the requested port."""

    env = os.environ.copy()
    env["APP_DATA_MODE"] = "synthetic"
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.runOnSave",
        "false",
        "--browser.gatherUsageStats",
        "false",
        "--theme.base",
        "dark",
        "--theme.backgroundColor",
        "#0E1117",
        "--theme.secondaryBackgroundColor",
        "#262730",
        "--theme.textColor",
        "#FAFAFA",
        "--theme.primaryColor",
        "#FF4B4B",
    ]
    return subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _wait_for_server(
    base_url: str,
    process: subprocess.Popen[str],
    timeout_seconds: int = 60,
) -> None:
    """Wait until the Streamlit server responds."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Streamlit exited before screenshots could be taken.")
        try:
            with urllib.request.urlopen(base_url, timeout=2) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(1)

    raise TimeoutError("Timed out waiting for Streamlit to start.")


def _capture_pages(base_url: str, temp_dir: Path) -> None:
    """Capture each Streamlit page to a temporary directory."""

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            device_scale_factor=2,
            color_scheme="dark",
        )
        page = context.new_page()

        try:
            for title, path, filename, min_charts in SCREENSHOT_PAGES:
                _capture_one_page(
                    page,
                    base_url,
                    title,
                    path,
                    filename,
                    min_charts,
                    temp_dir,
                )
        finally:
            context.close()
            browser.close()


def _capture_one_page(
    page: Page,
    base_url: str,
    title: str,
    path: str,
    filename: str,
    min_charts: int,
    temp_dir: Path,
) -> None:
    """Navigate to one page, run safety checks, and capture a full-page image."""

    page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
    page.goto(f"{base_url}{path}", wait_until="domcontentloaded", timeout=60_000)
    _wait_for_render(page, title, min_charts)
    capture_height = _expand_streamlit_scroll_area(page)
    if capture_height > VIEWPORT_HEIGHT:
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": capture_height})
        page.wait_for_timeout(1_000)
    _assert_safe_synthetic_page(page, title)
    page.screenshot(path=temp_dir / filename, full_page=True)


def _wait_for_render(page: Page, title: str, min_charts: int) -> None:
    """Wait for Streamlit text, network quiet, and Plotly charts when present."""

    try:
        page.wait_for_load_state("networkidle", timeout=30_000)
    except TimeoutError:
        pass

    _sidebar_badge(page).wait_for(
        state="visible",
        timeout=30_000,
    )
    _ensure_sidebar_expanded(page)

    if title == "About":
        page.get_by_text("This is a student learning project", exact=False).wait_for(
            state="visible",
            timeout=30_000,
        )
    else:
        page.get_by_role("heading", name=title, exact=True).wait_for(
            state="visible",
            timeout=30_000,
        )

    if min_charts:
        _wait_for_plotly_charts(page, min_charts)
    page.wait_for_timeout(2_000)


def _ensure_sidebar_expanded(page: Page) -> None:
    """Ensure the Streamlit sidebar and synthetic badge are visible."""

    badge = _sidebar_badge(page)
    try:
        badge.wait_for(state="visible", timeout=2_000)
        return
    except TimeoutError:
        pass

    for label in ("keyboard_double_arrow_right", "Open sidebar"):
        button = page.get_by_role("button", name=label)
        if button.count():
            button.first.click(timeout=5_000)
            badge.wait_for(state="visible", timeout=10_000)
            return

    raise RuntimeError("Synthetic data badge is not visible; sidebar may be collapsed.")


def _sidebar_badge(page: Page):
    """Return the sidebar's synthetic data-mode badge locator."""

    return page.locator("[data-testid='stSidebarUserContent']").get_by_text(
        "Data mode: Synthetic (public demo)",
        exact=True,
    )


def _wait_for_plotly_charts(page: Page, expected_count: int) -> None:
    """Wait until the expected number of Plotly charts has rendered."""

    deadline = time.monotonic() + 30
    charts = page.locator(".js-plotly-plot")
    while time.monotonic() < deadline:
        if charts.count() >= expected_count:
            for index in range(expected_count):
                charts.nth(index).wait_for(state="visible", timeout=10_000)
            return
        page.wait_for_timeout(500)

    raise TimeoutError(f"Expected at least {expected_count} Plotly charts to render.")


def _assert_safe_synthetic_page(page: Page, title: str) -> None:
    """Abort if the page is not synthetic or contains private comparable names."""

    body_text = page.locator("body").inner_text(timeout=30_000)
    body_upper = body_text.upper()
    if "SYNTHETIC" not in body_upper:
        raise RuntimeError(f"{title}: page does not show synthetic data mode.")
    if "REAL ORBIS" in body_upper:
        raise RuntimeError(f"{title}: page appears to be in real Orbis mode.")

    leaked_names = [
        token for token in PRIVATE_COMPARABLE_NAME_TOKENS if token in body_upper
    ]
    if leaked_names:
        joined = ", ".join(leaked_names)
        raise RuntimeError(f"{title}: private comparable name(s) visible: {joined}")


def _expand_streamlit_scroll_area(page: Page) -> int:
    """Let Playwright full-page screenshots include Streamlit's scroll container."""

    target_height = page.evaluate("""
        () => {
          const main = document.querySelector("section[data-testid='stMain']");
          const appView = document.querySelector("[data-testid='stAppViewContainer']");
          const sidebar = document.querySelector("section[data-testid='stSidebar']");
          const targetHeight = Math.max(
            main?.scrollHeight || 0,
            document.documentElement.scrollHeight,
            document.body.scrollHeight,
            window.innerHeight
          );

          document.documentElement.style.height = "auto";
          document.documentElement.style.overflow = "visible";
          document.body.style.height = "auto";
          document.body.style.overflow = "visible";

          if (appView) {
            appView.style.height = "auto";
            appView.style.overflow = "visible";
          }
          if (main) {
            main.style.height = `${targetHeight}px`;
            main.style.maxHeight = "none";
            main.style.overflow = "visible";
          }
          if (sidebar) {
            sidebar.style.minHeight = `${targetHeight}px`;
          }
          return targetHeight;
        }
        """)
    page.wait_for_timeout(500)
    return int(target_height)


def _replace_screenshots(temp_dir: Path) -> None:
    """Atomically replace public screenshot files after all captures pass."""

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in SCREENSHOTS_DIR.glob("*.png"):
        file_path.unlink()
    for _, _, filename, _ in SCREENSHOT_PAGES:
        shutil.copy2(temp_dir / filename, SCREENSHOTS_DIR / filename)


def _stop_process(process: subprocess.Popen[str]) -> None:
    """Stop the temporary Streamlit process."""

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
