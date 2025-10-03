from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to the Streamlit app
            page.goto("http://localhost:8501", timeout=60000)

            # Wait for the file uploader to be visible
            file_uploader_locator = page.locator('input[type="file"]')
            expect(file_uploader_locator).to_be_visible(timeout=30000)

            # Upload the test CSV file
            file_path = "historical_data/snapshot_goldoct190925.csv"
            page.set_input_files('input[type="file"]', file_path)

            # Wait for the file to be registered by Streamlit
            page.wait_for_timeout(2000)

            # Click the "Load CSV Data" button
            load_button = page.get_by_role("button", name="Load CSV Data")
            expect(load_button).to_be_enabled(timeout=10000)
            load_button.click()

            # Wait for the "Running" indicator to appear and then disappear
            running_indicator = page.locator('[data-testid="stStatusWidget"]')
            expect(running_indicator).to_be_visible(timeout=10000)
            expect(running_indicator).to_be_hidden(timeout=90000)

            # Wait for the option chain table to be rendered
            option_table_locator = page.locator(".option-table-container")
            expect(option_table_locator).to_be_visible(timeout=30000)

            # Wait for charts to potentially load
            page.wait_for_timeout(5000)

            # Take a screenshot of the main content area
            # We screenshot the main page, not just the iframe content, to see the whole picture.
            main_content_locator = page.locator("section.main")
            main_content_locator.screenshot(path="jules-scratch/verification/verification.png")

            print("Verification script completed successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="jules-scratch/verification/error.png")

        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()