
import sys
import asyncio
import time
from pyppeteer import launch

if len(sys.argv) != 2:
    print("usage : [filename.html]")
    sys.exit(1)

file = sys.argv[1]
outfile = file.replace(".html", ".jpg")


async def main():
    browser = await launch()
    page = await browser.newPage()
    await page.goto('https://storage.googleapis.com/perplexus/public/{}'.format(file))
    # we need to wait for the background to load
    time.sleep(1)
    await page.screenshot({'path': outfile, 'fullPage': 'false',
                           'type': 'jpeg', 'quality': 50,
                           'clip' : {
                               'x': 0, 'y': 0,
                               'width': 600, 'height': 600
                           }})
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
