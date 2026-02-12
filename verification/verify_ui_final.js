const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const filePath = 'file://' + path.resolve('frontend/index.html');
  await page.goto(filePath);
  await page.waitForTimeout(1000);

  // Inject some mock clips to see how they look
  await page.evaluate(() => {
    // Check if displayClips exists in global scope
    if (typeof window.displayClips === 'function') {
        const clips = [
            { title: "Epic Play", description: "Streamer does something amazing!", rating: 9.5, start: 125, end: 155, twitch_url: "https://twitch.tv/test?t=0h2m5s" }
        ];
        window.displayClips(clips);
    }
  });

  await page.screenshot({ path: 'verification/final_ui_check.png', fullPage: true });
  await browser.close();
})();
