const POST_WIDTH = 1080;
const POST_HEIGHT = 1350;
const TITLE_SIDE_MARGIN = 32;
const TITLE_STRETCH = 1.08;

const screens = Array.from(document.querySelectorAll(".step-screen"));
const dotContainers = Array.from(document.querySelectorAll(".step-dots"));
const uploadBox = document.getElementById("uploadBox");
const imageInput = document.getElementById("imageInput");
const titleInput = document.getElementById("titleInput");
const titleCount = document.getElementById("titleCount");
const titleNextButton = document.getElementById("titleNextButton");
const canvasCard = document.getElementById("canvasCard");
const canvas = document.getElementById("postCanvas");
const ctx = canvas.getContext("2d");
const imageZone = document.getElementById("imageZone");
const titleZone = document.getElementById("titleZone");
const zoomRange = document.getElementById("zoomRange");
const xRange = document.getElementById("xRange");
const yRange = document.getElementById("yRange");
const titleRange = document.getElementById("titleRange");
const zoomValue = document.getElementById("zoomValue");
const xValue = document.getElementById("xValue");
const yValue = document.getElementById("yValue");
const titleSizeValue = document.getElementById("titleSizeValue");
const finishButton = document.getElementById("finishButton");
const resultImage = document.getElementById("resultImage");
const downloadButton = document.getElementById("downloadButton");
const newPostButton = document.getElementById("newPostButton");

const state = {
  step: 1,
  image: null,
  zoom: 1,
  offsetX: 0,
  offsetY: 0,
  titleOffsetY: 0,
  titleSize: 28,
  dragging: null,
  dragStartX: 0,
  dragStartY: 0,
  startOffsetX: 0,
  startOffsetY: 0,
  startTitleOffsetY: 0,
  resultUrl: ""
};

function renderDots() {
  dotContainers.forEach((container) => {
    container.innerHTML = "";
    for (let index = 1; index <= 4; index += 1) {
      const dot = document.createElement("span");
      if (index < state.step) dot.className = "is-done";
      if (index === state.step) dot.className = "is-current";
      container.appendChild(dot);
    }
  });
}

function goToStep(step) {
  state.step = step;
  screens.forEach((screen) => {
    screen.classList.toggle("is-active", Number(screen.dataset.step) === step);
  });
  renderDots();
  if (step === 3) drawPost();
}

function updateControls() {
  titleCount.textContent = String(titleInput.value.length);
  titleNextButton.disabled = !titleInput.value.trim();
  zoomValue.textContent = `${Math.round(state.zoom * 100)}%`;
  xValue.textContent = String(Math.round(state.offsetX));
  yValue.textContent = String(Math.round(state.offsetY));
  titleSizeValue.textContent = `${state.titleSize}px`;
}

function setOffsets(x, y) {
  state.offsetX = Math.max(-540, Math.min(540, Number(x)));
  state.offsetY = Math.max(-675, Math.min(675, Number(y)));
  xRange.value = String(state.offsetX);
  yRange.value = String(state.offsetY);
  updateControls();
  drawPost();
}

function wrapText(text, maxWidth) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";

  words.forEach((word) => {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = test;
    }
  });

  if (line) lines.push(line);
  return lines;
}

function fitTitle(text) {
  let size = state.titleSize * (POST_WIDTH / 420);
  let lines = [];
  const maxWidth = (POST_WIDTH - TITLE_SIDE_MARGIN * 2) / TITLE_STRETCH;

  while (size >= 26) {
    ctx.font = `900 ${size}px Arial Black, Impact, Montserrat, Arial, sans-serif`;
    lines = text.split(/\n+/).flatMap((part) => wrapText(part, maxWidth));
    if (lines.length <= 4 && lines.every((line) => ctx.measureText(line).width <= maxWidth)) break;
    size -= 4;
  }

  return { size, lines };
}

function drawPlaceholder() {
  ctx.fillStyle = "#101010";
  ctx.fillRect(0, 0, POST_WIDTH, POST_HEIGHT);

  const glow = ctx.createRadialGradient(POST_WIDTH / 2, 360, 80, POST_WIDTH / 2, 360, 760);
  glow.addColorStop(0, "rgba(255, 214, 0, 0.22)");
  glow.addColorStop(1, "rgba(255, 214, 0, 0)");
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, POST_WIDTH, POST_HEIGHT);

  ctx.fillStyle = "#ffd600";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.font = "900 34px Montserrat, Arial, sans-serif";
  ctx.fillText("VILA MASCOTE", POST_WIDTH / 2, POST_HEIGHT / 2 - 22);
  ctx.fillStyle = "rgba(255, 255, 255, 0.56)";
  ctx.font = "700 24px Montserrat, Arial, sans-serif";
  ctx.fillText("adicione uma foto", POST_WIDTH / 2, POST_HEIGHT / 2 + 26);
}

function drawImage() {
  if (!state.image) {
    drawPlaceholder();
    return;
  }

  const baseScale = Math.max(POST_WIDTH / state.image.width, POST_HEIGHT / state.image.height);
  const scale = baseScale * state.zoom;
  const width = state.image.width * scale;
  const height = state.image.height * scale;
  const x = (POST_WIDTH - width) / 2 + state.offsetX;
  const y = (POST_HEIGHT - height) / 2 + state.offsetY;

  ctx.drawImage(state.image, x, y, width, height);
}

function drawOverlay() {
  const dark = ctx.createLinearGradient(0, POST_HEIGHT * 0.35, 0, POST_HEIGHT);
  dark.addColorStop(0, "rgba(0, 0, 0, 0)");
  dark.addColorStop(0.25, "rgba(0, 0, 0, 0.60)");
  dark.addColorStop(0.50, "rgba(0, 0, 0, 0.90)");
  dark.addColorStop(0.70, "rgba(0, 0, 0, 0.97)");
  dark.addColorStop(1, "rgba(0, 0, 0, 1)");
  ctx.fillStyle = dark;
  ctx.fillRect(0, 0, POST_WIDTH, POST_HEIGHT);
}

function drawTitle() {
  const stripHeight = POST_HEIGHT * 0.18;
  const lineY = POST_HEIGHT * 0.65;
  const lineMargin = 72;
  const handle = "@vila.mascote";

  ctx.save();
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, POST_HEIGHT - stripHeight, POST_WIDTH, stripHeight);

  ctx.font = "700 38px Arial, sans-serif";
  const handleWidth = ctx.measureText(handle).width + 16;
  const sideWidth = (POST_WIDTH - lineMargin * 2 - handleWidth - 56) / 2;
  ctx.strokeStyle = "#ffd600";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(lineMargin, lineY);
  ctx.lineTo(lineMargin + sideWidth, lineY);
  ctx.stroke();
  ctx.fillStyle = "#ffd600";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(handle, POST_WIDTH / 2, lineY);
  ctx.beginPath();
  ctx.moveTo(POST_WIDTH - lineMargin - sideWidth, lineY);
  ctx.lineTo(POST_WIDTH - lineMargin, lineY);
  ctx.stroke();
  ctx.restore();

  const title = titleInput.value.trim().toLocaleUpperCase("pt-BR");
  if (!title) return;

  const { size, lines } = fitTitle(title);
  const lineHeight = size * 1.1;
  const totalHeight = lines.length * lineHeight;
  const areaTop = lineY + 48;
  const areaBottom = POST_HEIGHT - stripHeight - 20;
  const baseY = areaTop + (areaBottom - areaTop - totalHeight) / 2 + state.titleOffsetY;

  ctx.save();
  ctx.fillStyle = "#ffd600";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.font = `900 ${size}px Arial Black, Impact, Montserrat, Arial, sans-serif`;
  lines.forEach((line, index) => {
    const y = baseY + index * lineHeight;
    const naturalWidth = ctx.measureText(line).width;
    const safeWidth = POST_WIDTH - TITLE_SIDE_MARGIN * 2;
    const scaleX = Math.min(TITLE_STRETCH, safeWidth / Math.max(naturalWidth, 1));
    ctx.save();
    ctx.translate(POST_WIDTH / 2, y);
    ctx.scale(scaleX, 1);
    ctx.fillText(line, 0, 0);
    ctx.restore();
  });
  ctx.restore();
}

function drawPost() {
  ctx.clearRect(0, 0, POST_WIDTH, POST_HEIGHT);
  drawImage();
  drawOverlay();
  drawTitle();
}

function makeResult() {
  drawPost();
  state.resultUrl = canvas.toDataURL("image/png");
  resultImage.src = state.resultUrl;
  downloadButton.href = state.resultUrl;
  goToStep(4);
}

uploadBox.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", () => {
  const file = imageInput.files && imageInput.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    const img = new Image();
    img.onload = () => {
      state.image = img;
      state.zoom = 1;
      zoomRange.value = "100";
      setOffsets(0, 0);
      goToStep(2);
      titleInput.focus();
    };
    img.src = String(reader.result);
  };
  reader.readAsDataURL(file);
});

titleInput.addEventListener("input", () => {
  updateControls();
  drawPost();
});

titleNextButton.addEventListener("click", () => {
  if (!titleInput.value.trim()) return;
  goToStep(3);
});

zoomRange.addEventListener("input", () => {
  state.zoom = Number(zoomRange.value) / 100;
  updateControls();
  drawPost();
});

xRange.addEventListener("input", () => setOffsets(xRange.value, state.offsetY));
yRange.addEventListener("input", () => setOffsets(state.offsetX, yRange.value));
titleRange.addEventListener("input", () => {
  state.titleSize = Number(titleRange.value);
  updateControls();
  drawPost();
});

document.querySelectorAll("[data-go-step]").forEach((button) => {
  button.addEventListener("click", () => goToStep(Number(button.dataset.goStep)));
});

function getCanvasPoint(event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((event.clientX - rect.left) / rect.width) * POST_WIDTH,
    y: ((event.clientY - rect.top) / rect.height) * POST_HEIGHT
  };
}

function startDrag(event, target) {
  if (!state.image) return;
  event.preventDefault();
  event.currentTarget.setPointerCapture(event.pointerId);
  const point = getCanvasPoint(event);
  state.dragging = target;
  state.dragStartX = point.x;
  state.dragStartY = point.y;
  state.startOffsetX = state.offsetX;
  state.startOffsetY = state.offsetY;
  state.startTitleOffsetY = state.titleOffsetY;
  canvasCard.classList.add("is-dragging");
}

imageZone.addEventListener("pointerdown", (event) => startDrag(event, "image"));
titleZone.addEventListener("pointerdown", (event) => startDrag(event, "title"));

function moveDrag(event) {
  if (!state.dragging) return;
  event.preventDefault();
  const point = getCanvasPoint(event);
  if (state.dragging === "title") {
    state.titleOffsetY = state.startTitleOffsetY + point.y - state.dragStartY;
    updateControls();
    drawPost();
    return;
  }

  setOffsets(state.startOffsetX + point.x - state.dragStartX, state.startOffsetY + point.y - state.dragStartY);
}

imageZone.addEventListener("pointermove", moveDrag);
titleZone.addEventListener("pointermove", moveDrag);

function stopDragging() {
  state.dragging = null;
  canvasCard.classList.remove("is-dragging");
}

[imageZone, titleZone].forEach((zone) => {
  zone.addEventListener("pointerup", stopDragging);
  zone.addEventListener("pointercancel", stopDragging);
  zone.addEventListener("lostpointercapture", stopDragging);
  zone.addEventListener("pointerleave", stopDragging);
});

finishButton.addEventListener("click", makeResult);

downloadButton.addEventListener("click", (event) => {
  if (!downloadButton.href || downloadButton.href.endsWith("#")) {
    event.preventDefault();
  }
});

newPostButton.addEventListener("click", () => {
  imageInput.value = "";
  titleInput.value = "";
  state.image = null;
  state.zoom = 1;
  state.titleOffsetY = 0;
  state.titleSize = 28;
  state.resultUrl = "";
  resultImage.removeAttribute("src");
  downloadButton.href = "#";
  zoomRange.value = "100";
  titleRange.value = "28";
  setOffsets(0, 0);
  goToStep(1);
});

if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(drawPost);
}

updateControls();
goToStep(1);
drawPost();
