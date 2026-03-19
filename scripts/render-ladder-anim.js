import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const html = path.resolve(__dirname, "../ladder_anim.html");
const framesDir = path.resolve(__dirname, "../frames");
const outDir = path.resolve(__dirname, "../assets/why");
fs.mkdirSync(framesDir, { recursive: true });
fs.mkdirSync(outDir, { recursive: true });

// Animation parameters
const W = 1200, H = 700;
const fps = 15;
const seconds = 8;            // loop length
const N = fps * seconds;      // frame count
const DPR = 2;                // retina quality

(async () => {
  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: DPR });

  for (let i = 0; i < N; i++) {
    const t = (i / (N - 1)); // 0..1
    const url = `file://${html}?t=${t.toFixed(5)}`;
    await page.goto(url, { waitUntil: "networkidle0" });

    const sel = "#ladderChart";
    await page.waitForSelector(sel);
    const canvas = await page.$(sel);
    const file = path.join(framesDir, `frame_${String(i).padStart(3, "0")}.png`);
    await canvas.screenshot({ path: file });
    process.stdout.write(`\rRendered ${i+1}/${N}`);
  }
  console.log("\nDone.");
  await browser.close();
})();
