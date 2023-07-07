
import time
import sys
from playwright.sync_api import sync_playwright

if len(sys.argv) < 2:
    print("usage : [filename.html]")
    sys.exit(1)

def main(files:[]):
    with sync_playwright() as browser_controller:
        browser = browser_controller.chromium.launch()
        for file in files:
            print(f"processing {file}")
            outfile = file.replace(".html", ".jpg")
            page = browser.new_page()
            page.goto('https://storage.googleapis.com/perplexus/public/{}'.format(file))
            time.sleep(1)
            page.screenshot(path=outfile,
                            full_page=False,
                            type="jpeg",
                            quality=50,
                            clip={
                                       'x': 200, 'y': 0,
                                       'width': 900, 'height': 900
                                   },
                            scale="device",
                            )

if __name__ == "__main__":
    main(sys.argv[1:])
