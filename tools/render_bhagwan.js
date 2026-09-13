const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const TEMPLATE = path.join(ROOT, "templates", "bhagwan_vichaar.html");
const manifestPath = process.argv[2] || path.join(ROOT, "work", "manifest.json");
const outputPath = process.argv[3] || path.join(ROOT, "work", "silent.mp4");

if (!fs.existsSync(TEMPLATE)) throw new Error(`Template not found: ${TEMPLATE}`);
if (!fs.existsSync(manifestPath)) throw new Error(`Manifest not found: ${manifestPath}`);

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));

function fileUrl(relativePath) {
  if (!relativePath) return "";
  const absolute = path.isAbsolute(relativePath) ? relativePath : path.join(ROOT, relativePath);
  if (!fs.existsSync(absolute)) throw new Error(`Visual image not found: ${absolute}`);
  return "file://" + encodeURI(absolute.replace(/\\/g, "/"));
}

function makeStory() {
  return {
    series: { name: "DIVINE VAANI", mark: "ॐ", kicker: "BHAGWAN VICHAAR", tagline: "DEVOTIONAL STORY" },
    theme: { imageOpacity: "0.25" },
    intro: {
      image: fileUrl("visuals/common/intro.jpg"),
      kicker: "BHAGWAN VICHAAR",
      title: manifest.title || "भगवान का एक विचार",
      subtitle: manifest.subtitle || "",
      duration: 5
    },
    scenes: (manifest.scenes || []).map((s, i) => ({
      chapter: s.chapter || "विचार",
      title: s.title || s.chapter || "विचार",
      text: s.text || s.narration || "",
      image: fileUrl(s.visual_path),
      textPosition: ["left", "right", "center"][i % 3],
      deity: s.deity || "भगवान",
      label: s.label || "विचार",
      number: s.number || i + 1,
      duration: Number(s.duration) || 8,
      zoom: s.zoom || "1.04"
    })),
    outro: {
      image: fileUrl("visuals/common/outro.jpg"),
      kicker: "आज का विचार",
      title: manifest.ending?.title || "एक पल ठहरिए",
      subtitle: manifest.ending?.subtitle || "",
      duration: 5
    }
  };
}

async function main() {
  const template = fs.readFileSync(TEMPLATE, "utf8");
  const story = makeStory();
  const injected = `<script>window.BHAGWAN_STORY=${JSON.stringify(story)};</script>`;
  const html = template.replace("</head>", injected + "</head>");
  const renderedHtml = path.join(ROOT, "work", "rendered_bhagwan.html");
  fs.writeFileSync(renderedHtml, html, "utf8");

  const browser = await chromium.launch({
    headless: true,
    args: ["--allow-file-access-from-files"]
  });

  const page = await browser.newPage({
    viewport: { width: 1080, height: 1920 },
    deviceScaleFactor: 1
  });

  await page.goto("file://" + renderedHtml.replace(/\\/g, "/"), { waitUntil: "load" });

  await page.addInitScript(({ story }) => {
    window.BHAGWAN_STORY = story;
  }, { story });

  await page.waitForTimeout(300);

  const slideCount = await page.locator(".slide").count();
  if (slideCount < 1) throw new Error("Template did not render any slides.");

  const fps = 30;
  const durations = [
    story.intro.duration,
    ...story.scenes.map(s => s.duration),
    story.outro.duration
  ];

  const framesDir = path.join(ROOT, "work", "frames");
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });

  // Use the original template's slide layout; reveal one slide at a time.
  let frameNo = 0;
  const totalSlides = await page.locator(".slide").count();

  for (let i = 0; i < totalSlides; i++) {
    await page.evaluate(index => {
      const slides = [...document.querySelectorAll(".slide")];
      slides.forEach((el, n) => {
        el.style.display = n === index ? "block" : "none";
        el.classList.toggle("active", n === index);
      });
      window.scrollTo(0, 0);
    }, i);

    await page.waitForTimeout(250);

    const duration = Number(durations[i] || 8);
    const frames = Math.max(1, Math.round(duration * fps));
    const start = Date.now();

    for (let f = 0; f < frames; f++) {
      const target = start + (f * 1000) / fps;
      const wait = target - Date.now();
      if (wait > 0) await new Promise(r => setTimeout(r, wait));
      const frame = path.join(framesDir, `frame_${String(frameNo).padStart(7, "0")}.png`);
      await page.screenshot({ path: frame, type: "png" });
      frameNo++;
    }
  }

  await browser.close();

  const result = spawnSync("ffmpeg", [
    "-y", "-framerate", String(fps),
    "-i", path.join(framesDir, "frame_%07d.png"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", outputPath
  ], { stdio: "inherit" });

  if (result.status !== 0) throw new Error("FFmpeg encoding failed.");
  console.log(`VIDEO READY: ${outputPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
