import { chromium } from 'playwright';
(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
    await page.goto('http://localhost:5173/');
    await page.fill('input[name="body"]', 'What is the weather in Tokyo?');
    await page.click('button[type="submit"]');
    console.log('Submitted form, waiting for results...');
    await page.waitForTimeout(40000);
    const html = await page.evaluate(() => {
        const app = document.querySelector('secure-iframe-app');
        return app ? app.shadowRoot.innerHTML : 'No app found';
    });
    console.log('FINAL HTML SNIPPET:', html.substring(0, 2000));
    await browser.close();
})();
