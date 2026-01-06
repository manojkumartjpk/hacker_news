const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const pairs = [
  {
    name: 'home',
    local: 'http://localhost:3000/',
    hn: 'https://news.ycombinator.com/',
  },
  {
    name: 'past',
    local: 'http://localhost:3000/?sort=past',
    hn: 'https://news.ycombinator.com/front',
  },
  {
    name: 'comments',
    local: 'http://localhost:3000/comments',
    hn: 'https://news.ycombinator.com/newcomments',
  },
  {
    name: 'post-2',
    local: 'http://localhost:3000/post/2',
    hn: 'https://news.ycombinator.com/item?id=46497712',
  },
];

(async () => {
  const outDir = path.resolve(__dirname, '..', '.screenshots');
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });

  for (const pair of pairs) {
    await page.goto(pair.local, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(outDir, `local-${pair.name}-viewport.png`),
      fullPage: false,
    });
    await page.screenshot({
      path: path.join(outDir, `local-${pair.name}-full.png`),
      fullPage: true,
    });

    await page.goto(pair.hn, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(outDir, `hn-${pair.name}-viewport.png`),
      fullPage: false,
    });
    await page.screenshot({
      path: path.join(outDir, `hn-${pair.name}-full.png`),
      fullPage: true,
    });
  }

  await browser.close();
  console.log(`Saved screenshots to ${outDir}`);
})();
