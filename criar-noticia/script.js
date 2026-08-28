const POST_WIDTH = 1080;
const POST_HEIGHT = 1350;

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
const zoomRange = document.getElementById("zoomRange");
const xRange = document.getElementById("xRange");
const yRange = document.getElementById("yRange");
const zoomValue = document.getElementById("zoomValue");
const xValue = document.getElementById("xValue");
const yValue = document.getElementById("yValue");
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
  dragging: false,
  dragStartX: 0,
  dragStartY: 0,
  startOffsetX: 0,
  startOffsetY: 0,
  resultUrl: ""
};

const logo = new Image();
logo.src = "../assets/logo-vila-mascote.png";
logo.onload = drawPost;

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
  let size = 92;
  let lines = [];
  const maxWidth = POST_WIDTH - 120;

  while (size >= 48) {
    ctx.font = `900 ${size}px Montserrat, Arial Black, Arial, sans-serif`;
    lines = text.split(/\n+/).flatMap((part) => wrapText(part, maxWidth));
    if (lines.length <= 5 && lines.every((line) => ctx.measureText(line).width <= maxWidth)) break;
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
  const dark = ctx.createLinearGradient(0, POST_HEIGHT * 0.24, 0, POST_HEIGHT);
  dark.addColorStop(0, "rgba(0, 0, 0, 0)");
  dark.addColorStop(0.32, "rgba(0, 0, 0, 0.34)");
  dark.addColorStop(0.58, "rgba(0, 0, 0, 0.82)");
  dark.addColorStop(1, "rgba(0, 0, 0, 1)");
  ctx.fillStyle = dark;
  ctx.fillRect(0, 0, POST_WIDTH, POST_HEIGHT);

  const brand = ctx.createLinearGradient(0, POST_HEIGHT * 0.5, POST_WIDTH, POST_HEIGHT);
  brand.addColorStop(0, "rgba(16, 35, 71, 0.25)");
  brand.addColorStop(0.6, "rgba(16, 35, 71, 0.55)");
  brand.addColorStop(1, "rgba(255, 214, 0, 0.2)");
  ctx.fillStyle = brand;
  ctx.fillRect(0, 0, POST_WIDTH, POST_HEIGHT);
}

function drawBrandMark() {
  const size = 58;
  const x = POST_WIDTH - 96;
  const y = 54;

  ctx.save();
  ctx.globalAlpha = 0.86;
  if (logo.complete && logo.naturalWidth) {
    ctx.drawImage(logo, x, y, size, size);
  }
  ctx.restore();
}

function drawTitle() {
  const title = titleInput.value.trim().toLocaleUpperCase("pt-BR") || "TÍTULO DA NOTÍCIA";
  const { size, lines } = fitTitle(title);
  const lineHeight = size * 1.08;
  const titleBottom = POST_HEIGHT - 138;
  const startY = titleBottom - lines.length * lineHeight;

  ctx.save();
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillStyle = "#ffffff";
  ctx.shadowColor = "rgba(0, 0, 0, 0.55)";
  ctx.shadowBlur = 18;
  ctx.shadowOffsetY = 6;
  ctx.font = `900 ${size}px Montserrat, Arial Black, Arial, sans-serif`;
  lines.forEach((line, index) => {
    ctx.fillText(line, 60, startY + index * lineHeight);
  });
  ctx.restore();

  ctx.fillStyle = "#ffd600";
  ctx.fillRect(60, POST_HEIGHT - 92, 184, 8);
  ctx.font = "900 28px Montserrat, Arial, sans-serif";
  ctx.fillText("@VILA.MASCOTE", 60, POST_HEIGHT - 52);
}

function drawPost() {
  ctx.clearRect(0, 0, POST_WIDTH, POST_HEIGHT);
  drawImage();
  drawOverlay();
  drawBrandMark();
  drawTitle();
}

function makeResult() {
  drawPost();
  if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
  canvas.toBlob((blob) => {
    state.resultUrl = URL.createObjectURL(blob);
    resultImage.src = state.resultUrl;
    downloadButton.href = state.resultUrl;
    goToStep(4);
  }, "image/png");
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

canvas.addEventListener("pointerdown", (event) => {
  if (!state.image) return;
  event.preventDefault();
  canvas.setPointerCapture(event.pointerId);
  const point = getCanvasPoint(event);
  state.dragging = true;
  state.dragStartX = point.x;
  state.dragStartY = point.y;
  state.startOffsetX = state.offsetX;
  state.startOffsetY = state.offsetY;
  canvasCard.classList.add("is-dragging");
});

canvas.addEventListener("pointermove", (event) => {
  if (!state.dragging) return;
  event.preventDefault();
  const point = getCanvasPoint(event);
  setOffsets(
    state.startOffsetX + point.x - state.dragStartX,
    state.startOffsetY + point.y - state.dragStartY
  );
});

function stopDragging() {
  state.dragging = false;
  canvasCard.classList.remove("is-dragging");
}

canvas.addEventListener("pointerup", stopDragging);
canvas.addEventListener("pointercancel", stopDragging);
canvas.addEventListener("lostpointercapture", stopDragging);
canvas.addEventListener("pointerleave", stopDragging);

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
  if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
  state.resultUrl = "";
  resultImage.removeAttribute("src");
  downloadButton.href = "#";
  zoomRange.value = "100";
  setOffsets(0, 0);
  goToStep(1);
});

if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(drawPost);
}

updateControls();
goToStep(1);
drawPost();
