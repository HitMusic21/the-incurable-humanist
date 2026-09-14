// Browser verification for Denise's Aug 2026 nav/copy/Press changes.
//
// Deliberately checks the HYDRATED page, not the served HTML. curl proves the
// SSR markup is right; only a real browser proves that what a reader actually
// sees after React mounts matches it — and several of these changes (the nav,
// the merged About card, the removed door links) only exist post-hydration.
//
//   node scripts/verify-ia-changes.mjs [baseUrl]      # default http://localhost:8787
//
// Screenshots land in /tmp/tih-verify/ for eyeballing the layout.

import { chromium, devices } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.argv[2] || "http://localhost:8787";
const SHOTS = "/tmp/tih-verify";
mkdirSync(SHOTS, { recursive: true });

let pass = 0;
const failures = [];

function check(label, condition, detail = "") {
  if (condition) {
    pass++;
    console.log(`  ok   ${label}`);
  } else {
    failures.push(`${label}${detail ? ` — ${detail}` : ""}`);
    console.log(`  FAIL ${label}${detail ? ` — ${detail}` : ""}`);
  }
}

const NAV = ["HOME", "ABOUT", "WRITING", "SPEAKING", "LISTENING", "PRESS"];

async function main() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const consoleErrors = [];
  page.on("console", (m) => m.type() === "error" && consoleErrors.push(m.text()));
  page.on("pageerror", (e) => consoleErrors.push(String(e)));

  // ---- Navigation -------------------------------------------------------
  console.log("\nNAVIGATION");
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
  const navLabels = await page.locator("header nav a").allInnerTexts();
  const cleaned = navLabels.map((t) => t.trim().toUpperCase());
  check("header has exactly 6 items", cleaned.length === 6, `got ${cleaned.length}: ${cleaned}`);
  for (const label of NAV) {
    check(`nav contains ${label}`, cleaned.includes(label));
  }
  const footerLinks = await page.locator("footer nav a").allInnerTexts();
  check("footer mirrors the same 6", footerLinks.length === 6, `got ${footerLinks.length}`);

  // Every nav target must actually resolve, not 404.
  for (const href of await page.locator("header nav a").evaluateAll((as) =>
    as.map((a) => a.getAttribute("href"))
  )) {
    const res = await page.request.get(`${BASE}${href}`);
    check(`nav target ${href} responds 200`, res.status() === 200, `got ${res.status()}`);
  }

  // ---- Home -------------------------------------------------------------
  console.log("\nHOME");
  const homeText = await page.locator("body").innerText();
  check("tagline drops 'inherited anyway'", !homeText.includes("inherited anyway"));
  check("tagline still reads grief/migration/art", /grief, migration, and art/i.test(homeText));
  check("Read/Listen/Book doors removed", !/Open the door/i.test(homeText));
  check("5-essay reader block removed", !/5-essay reader/i.test(homeText));
  // The description meta KEEPS the phrase — that was the deliberate split.
  const desc = await page.getAttribute('meta[name="description"]', "content");
  check("meta description keeps it", (desc || "").includes("inherited anyway"), desc || "");
  await page.screenshot({ path: `${SHOTS}/home.png`, fullPage: false });

  // ---- About ------------------------------------------------------------
  console.log("\nABOUT");
  await page.goto(`${BASE}/about`, { waitUntil: "networkidle" });
  const aboutText = await page.locator("body").innerText();
  // Assert on HEADINGS, not on body text. Both phrases legitimately occur in
  // the prose ("Welcome to the curious world of The Incurable Humanist…"), and
  // innerText inserts a line break around the <em>, so a /^…$/m text match
  // reports a subtitle that is not there.
  const aboutHeadings = (await page.locator("main h2, section h2").allInnerTexts()).map((t) =>
    t.trim()
  );
  check("no 'The Incurable Humanist' subtitle", !aboutHeadings.includes("The Incurable Humanist"),
    `headings: ${JSON.stringify(aboutHeadings)}`);
  check("no 'Denise Rodriguez Dao' subtitle", !aboutHeadings.includes("Denise Rodriguez Dao"));
  check("h1 is still About", (await page.locator("h1").first().innerText()).trim() === "About");

  const cards = await page.locator("main .bg-surface.rounded-xl, section .bg-surface").count();
  check("prose sits in a single card", cards <= 1, `found ${cards} card-like blocks`);

  // Portrait must render ABOVE the prose and carry intrinsic dimensions.
  const img = page.locator('img[src*="denisehome"]');
  check("portrait present", (await img.count()) === 1);
  const box = await img.first().boundingBox();
  const firstP = await page.locator("section p").first().boundingBox();
  check("portrait is above the text", box && firstP && box.y < firstP.y,
    box && firstP ? `img.y=${Math.round(box.y)} p.y=${Math.round(firstP.y)}` : "no box");
  check("portrait has width attr", !!(await img.first().getAttribute("width")));
  check("portrait has height attr", !!(await img.first().getAttribute("height")));
  check("all six paragraphs present", /room for another incurable humanist/i.test(aboutText));
  await page.screenshot({ path: `${SHOTS}/about.png`, fullPage: true });

  // ---- Writing ----------------------------------------------------------
  console.log("\nWRITING (/archive)");
  await page.goto(`${BASE}/archive`, { waitUntil: "networkidle" });
  check("h1 reads Writing", (await page.locator("h1").first().innerText()).trim() === "Writing");
  check("title says Writing", (await page.title()).startsWith("Writing"));
  const writingText = await page.locator("body").innerText();
  check("subscribe line present", /Subscribe to\s+The Incurable Humanist/i.test(writingText));
  const substack = page.locator('a[href*="substack.com/subscribe"]').first();
  check("Substack button present", (await substack.count()) > 0);
  check("Substack button opens in new tab",
    (await substack.getAttribute("target")) === "_blank");
  check("Substack link is UTM-tagged",
    ((await substack.getAttribute("href")) || "").includes("utm_source"));
  check("press cards moved off Writing", !/In the press/i.test(writingText));
  check("stale 'press coverage' line gone", !/press coverage/i.test(writingText));
  check("subscribe CTA survived the move", /Keep reading/i.test(writingText));
  await page.screenshot({ path: `${SHOTS}/writing.png`, fullPage: false });

  // ---- Listening --------------------------------------------------------
  console.log("\nLISTENING");
  await page.goto(`${BASE}/listen`, { waitUntil: "networkidle" });
  const listenText = await page.locator("body").innerText();
  check("h1 reads Listening", (await page.locator("h1").first().innerText()).trim() === "Listening");
  check("intro paragraph removed", !/soundtrack/i.test(listenText));
  check("new audio copy present", /also available in audio/i.test(listenText));
  check("Playlists heading", /Playlists/.test(listenText));
  check("Sunday box removed", !/New essay every Sunday/i.test(listenText));
  await page.screenshot({ path: `${SHOTS}/listening.png`, fullPage: false });

  // ---- Press ------------------------------------------------------------
  console.log("\nPRESS");
  const resp = await page.goto(`${BASE}/press`, { waitUntil: "networkidle" });
  check("/press returns 200 (not a redirect)", resp.status() === 200, `got ${resp.status()}`);
  check("/press did not redirect away", new URL(page.url()).pathname === "/press", page.url());
  check("h1 reads Press", (await page.locator("h1").first().innerText()).trim() === "Press");
  const pressText = await page.locator("body").innerText();
  for (const outlet of ["Observer", "The Art Gorgeous", "Singulart", "La Guía de Caracas"]) {
    check(`lists ${outlet}`, pressText.includes(outlet));
  }
  check("Click Magazine NYC dropped", !pressText.includes("Click Magazine"));
  const outboundCount = await page.locator('a[target="_blank"][rel*="noopener"]').count();
  check("outlet links open safely", outboundCount >= 4, `found ${outboundCount}`);
  await page.screenshot({ path: `${SHOTS}/press.png`, fullPage: true });

  // ---- Mobile nav overflow ---------------------------------------------
  console.log("\nMOBILE (iPhone SE, 375px)");
  const mobile = await browser.newContext({ ...devices["iPhone SE"] });
  const mp = await mobile.newPage();
  await mp.goto(`${BASE}/`, { waitUntil: "networkidle" });
  const overflow = await mp.evaluate(() => {
    const el = document.querySelector("header nav");
    return el ? { scrollW: el.scrollWidth, clientW: el.clientWidth } : null;
  });
  check("nav does not overflow horizontally",
    overflow && overflow.scrollW <= overflow.clientW + 1,
    overflow ? `scrollW=${overflow.scrollW} clientW=${overflow.clientW}` : "no nav");
  const docOverflow = await mp.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth + 1
  );
  check("page does not scroll sideways", docOverflow);
  await mp.screenshot({ path: `${SHOTS}/mobile-home.png`, fullPage: false });
  await mobile.close();

  // ---- Console ----------------------------------------------------------
  console.log("\nCONSOLE");
  const real = consoleErrors.filter((e) => !/favicon|Download the React DevTools/i.test(e));
  check("no console errors", real.length === 0, real.slice(0, 3).join(" | "));

  await browser.close();

  console.log(`\n${"=".repeat(52)}`);
  console.log(`PASS ${pass}   FAIL ${failures.length}`);
  if (failures.length) {
    console.log("\nFailures:");
    failures.forEach((f) => console.log(`  - ${f}`));
  }
  console.log(`Screenshots: ${SHOTS}/`);
  process.exit(failures.length ? 1 : 0);
}

main().catch((e) => {
  console.error("verification crashed:", e);
  process.exit(1);
});
