const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');

const pairs = [
  { name: 'home' },
  { name: 'past' },
  { name: 'comments' },
  { name: 'post-2' },
];

const outDir = path.resolve(__dirname, '..', '.screenshots');

const loadPng = (filePath) => {
  const data = fs.readFileSync(filePath);
  return PNG.sync.read(data);
};

const savePng = (png, filePath) => {
  const buffer = PNG.sync.write(png);
  fs.writeFileSync(filePath, buffer);
};

const diffPair = (name, pixelmatch) => {
  const localPath = path.join(outDir, `local-${name}-viewport.png`);
  const hnPath = path.join(outDir, `hn-${name}-viewport.png`);

  if (!fs.existsSync(localPath) || !fs.existsSync(hnPath)) {
    return { name, error: 'missing screenshot' };
  }

  const localImg = loadPng(localPath);
  const hnImg = loadPng(hnPath);

  const width = Math.min(localImg.width, hnImg.width);
  const height = Math.min(localImg.height, hnImg.height);

  const localCrop = new PNG({ width, height });
  const hnCrop = new PNG({ width, height });
  const diff = new PNG({ width, height });

  PNG.bitblt(localImg, localCrop, 0, 0, width, height, 0, 0);
  PNG.bitblt(hnImg, hnCrop, 0, 0, width, height, 0, 0);

  const diffPixels = pixelmatch(
    localCrop.data,
    hnCrop.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 }
  );

  const totalPixels = width * height;
  const diffPercent = (diffPixels / totalPixels) * 100;

  const diffPath = path.join(outDir, `diff-${name}-viewport.png`);
  savePng(diff, diffPath);

  return { name, width, height, diffPixels, diffPercent, diffPath };
};

(async () => {
  const { default: pixelmatch } = await import('pixelmatch');

  const results = pairs.map((pair) => diffPair(pair.name, pixelmatch));

  results.forEach((result) => {
    if (result.error) {
      console.log(`${result.name}: ${result.error}`);
      return;
    }
    console.log(
      `${result.name}: ${result.diffPercent.toFixed(2)}% diff ` +
      `(${result.diffPixels} px) -> ${path.relative(process.cwd(), result.diffPath)}`
    );
  });
})();
