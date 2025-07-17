<template>
  <div ref="canvasContainer" id="area" />
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue';
import { getWikiCodes, useRecentChange } from '../composition.js';
import { FixedLengthQueue, calc_rate_in_epm } from '../rate_measure.js';
import { loadSounds, calculateSize, playSound, playRandomSwell } from '../audio.js';
import { globalSettings, SPATIAL_POSITION, SPATIAL_PITCH } from '../global_settings.js';
import adjustAlpha from 'color-alpha';

const { recentChange } = useRecentChange();


// Colors and styles
const svg_background_color = '#1c2733';
const NEW_USER_BOX_COLOR = 'rgb(41, 128, 185)';
const new_user_color = 'rgb(205, 40, 214)';
const NEW_PAGE_COLOR = 'rgb(145, 212, 29)';
const TEXT_OUTLINE_COLOR = 'rgb(28, 39, 51)';
const TEXT_FILL_COLOR = 'rgb(255, 255, 255)';
const GROW_COLOR = '#2686cf';
const SHRINK_COLOR = '#de9332';

const CANVAS_DEFAULT_WIDTH = 1000;
const CANVAS_DEFAULT_HEIGHT = 600;

const CIRCLE_MAX_AGE = 60000;
const RING_MAX_AGE = 2500;
const TEXT_MAX_AGE = 3000;
const FLASH_MAX_AGE = 1000;
const NEW_USER_FADE_DELAY = 4000;
const NEW_USER_FADE_TIME = 3000;
const DEFAULT_ALPHA = 0.8;
const SILENT_ALPHA = 0.2;
const ARTICLE_TITLE_FONT_SIZE = 18;
const ARTICLE_TITLE_Y_ADJUST = 7;
const MAX_RATE_QUEUE_SIZE = 30;
const MAX_EVENT_AGE_FOR_RATE = 10 * 1000;
const UPDATE_RATE_EVERY = 3 * 1000;
const rateMeasureQueue = new FixedLengthQueue(MAX_RATE_QUEUE_SIZE);

const wikiCodeMap = new Map(getWikiCodes().map(item => [item.wikiCode, item]));

const drawables = reactive([]);

let canvasWidth = CANVAS_DEFAULT_WIDTH;
let canvasHeight = CANVAS_DEFAULT_HEIGHT;
let canvasDpr = window.devicePixelRatio || 1;
const canvasAspectRatio = canvasWidth/canvasHeight;
const canvasRef = ref(null);
let ctx;

let animationFrameId;
let lastRender = performance.now();
let epmDisplay = '';
let lastRateUpdate = 0;
let silent = false; // TODO update when volume or mute are changed


function drawRankItems( a, b ) {
  if (a.z < b.z) {return -1;} else if (a.z > b.z) {return 1;}
  if (a.timestamp < b.timestamp) {return -1;} else if (a.timestamp > b.timestamp) {return 1;}
  return 0;
}
function drawScene() {
  const now = performance.now();
  const delta = now - lastRender;
  lastRender = now;

  ctx.clearRect(0, 0, canvasWidth, canvasHeight);
  ctx.fillStyle = svg_background_color;
  ctx.fillRect(0, 0, canvasWidth, canvasHeight);

  const currentTime = Date.now();

  // Cleanup old drawables
  drawables.splice(0, drawables.length, ...drawables.filter((item) => currentTime - item.timestamp < item.maxAge));
  // console.debug(drawables.length + " items to draw");
  //drawables.sort(drawRankItems);

  // prune the drawables list
  //if (drawables.length > 200) drawables.shift();

  // draw the drawables
  const canvasSizeRatio = canvasWidth / CANVAS_DEFAULT_WIDTH;
  for (const item of drawables) {
    const age = currentTime - item.timestamp;

    if (item.type === 'circle') {
      const transformedItem = item.transform(item, age);
      ctx.beginPath();
      ctx.fillStyle = adjustAlpha(transformedItem.color, transformedItem.alpha);
      ctx.arc(transformedItem.x * canvasSizeRatio, transformedItem.y * canvasSizeRatio, transformedItem.r  * canvasSizeRatio, 0, 2 * Math.PI);
      ctx.fill();
    } else if (item.type === 'ring') {
      const transformedItem = item.transform(item, age);
      ctx.beginPath();
      ctx.fillStyle = adjustAlpha(transformedItem.color, transformedItem.alpha);
      ctx.arc(transformedItem.x * canvasSizeRatio, transformedItem.y * canvasSizeRatio, transformedItem.rOuter * canvasSizeRatio, 0, 2 * Math.PI);
      ctx.closePath();
      ctx.arc(transformedItem.x * canvasSizeRatio, transformedItem.y * canvasSizeRatio, transformedItem.rInner * canvasSizeRatio, 0, 2 * Math.PI, 1 /* counterclockwise */);
      ctx.closePath();
      ctx.fill();
    } else if (item.type === 'text') {
      const transformedItem = item.transform(item, age);
      // console.debug(`Item before transform: ${JSON.stringify(item)}`);
      // console.debug(`Item after transform: ${JSON.stringify(transformedItem)}`);
      const textFontSize = Math.floor(ARTICLE_TITLE_FONT_SIZE * canvasSizeRatio);
      const textFontYAdjust = ARTICLE_TITLE_Y_ADJUST;
      ctx.font = textFontSize + 'px sans-serif';
      ctx.textAlign = 'center';
      ctx.lineJoin = 'round';
      ctx.miterLimit = 2;

      // black outline
      ctx.lineWidth = 3 * canvasSizeRatio;
      ctx.strokeStyle = adjustAlpha(transformedItem.outlineColor, transformedItem.outlineAlpha);
      ctx.strokeText(transformedItem.text, transformedItem.x * canvasSizeRatio, (transformedItem.y + textFontYAdjust) * canvasSizeRatio);

      // white fill
      ctx.fillStyle = adjustAlpha(transformedItem.fillColor, transformedItem.fillAlpha);
      ctx.fillText(transformedItem.text, transformedItem.x * canvasSizeRatio, (transformedItem.y + textFontYAdjust) * canvasSizeRatio);

      // record metrics for hits later
      item.textMetrics = ctx.measureText(transformedItem.text);
    } else if (item.type === 'rectangle') {
      const transformedItem = item.transform(item, age);
      // console.debug(`Drawing rectangle: color ${transformedItem.fillColor}, alpha ${transformedItem.alpha}, ` +
      //     `(x, y): (${transformedItem.x}, ${transformedItem.y}), ` +
      //     `(width, height): (${transformedItem.width}, ${transformedItem.height})`);
      ctx.fillStyle = adjustAlpha(transformedItem.fillColor, transformedItem.alpha);
      ctx.fillRect(transformedItem.x * canvasSizeRatio, transformedItem.y * canvasSizeRatio, transformedItem.width * canvasSizeRatio, transformedItem.height * canvasSizeRatio);
    } else {
      console.warn(`Unrecognized item type ${item.type}. Item: ${JSON.stringify(item)}`);
    }

  }

  // Draw EPM display
  ctx.font = Math.floor(ARTICLE_TITLE_FONT_SIZE * canvasSizeRatio) + 'px sans-serif';
  ctx.textAlign = 'left';
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = 3 * canvasSizeRatio;
  ctx.strokeText(epmDisplay, 10 * canvasSizeRatio, canvasHeight - (10  * canvasSizeRatio));
  ctx.fillStyle = '#ffffff';
  ctx.fillText(epmDisplay, 10 * canvasSizeRatio, canvasHeight - (10  * canvasSizeRatio));
}

function loop() {
  const now = Date.now();
  if (now - lastRateUpdate > UPDATE_RATE_EVERY) {
    const epm = calc_rate_in_epm(rateMeasureQueue, now, MAX_EVENT_AGE_FOR_RATE);
    epmDisplay = `${epm} events per minute`;
    lastRateUpdate = now;
  }

  drawScene();
  animationFrameId = requestAnimationFrame(loop);
}

// easing functions from https://easings.net/
// inputs and outputs are: 0 <= x <= 1
function easeOutQuad(x) {
  return 1 - (1 - x) * (1 - x);
}

function easeOutExpo(x) {
  return x === 1 ? 1 : 1 - Math.pow(2, -10 * x);
}

function easeOutSqrt(x) {
  return Math.sqrt(x);
}

function easeOutLinear(x) {
  return x;
}

function handleRecentChange(change) {
  const timestamp = Date.now();
  const x = Math.random() * CANVAS_DEFAULT_WIDTH;
  const y = Math.random() * CANVAS_DEFAULT_HEIGHT;
  const [origSize, scaledSize] = calculateSize(change.data);
  // console.debug("Orig size: " + origSize + ", scaledSize: " + scaledSize);
  const color = change.data.event_type === 'new_page' ? NEW_PAGE_COLOR : (change.data.change_in_length > 0 ? GROW_COLOR : SHRINK_COLOR);

  // play the appropriate sound
  if (change.data.event_type === 'new_user') {
    playRandomSwell();
  } else {
    // play audio for the edit
    let pan = 0; // mono by default
    let calcPanFromPitch = false
    if (globalSettings.spatialAudio === SPATIAL_POSITION) {
      //console.log("Calculating pan from position");
      pan = x * 2 / CANVAS_DEFAULT_WIDTH - 1;
    } else if (globalSettings.spatialAudio === SPATIAL_PITCH) {
      //console.log("Setting flag to calculate pan from pitch");
      calcPanFromPitch = true;
    }

    if (origSize > 0) {
      playSound(scaledSize, 'add', pan, calcPanFromPitch)
    } else {
      playSound(scaledSize, 'sub', pan, calcPanFromPitch)
    }
  }

  // set up the drawables
  if (change.data.event_type === 'new_user') {
    const wikiName = wikiCodeMap.get(change.data.code).displayName;
    const messages = ['Welcome ' + change.data.user + ', ' + wikiName + '\'s newest user!',
      wikiName + ' has a new user, ' + change.data.user + '! Welcome!',
      'Welcome, ' + change.data.user + ' has joined ' + wikiName + '!'];
    const messageIndex = Math.round(Math.random() * (messages.length - 1));
    const message = messages[messageIndex];

    drawables.push({
      type: 'rectangle',
      x: 0,
      y: 0,
      z: 100,
      width: CANVAS_DEFAULT_WIDTH,
      height: 50,
      fillColor: NEW_USER_BOX_COLOR,
      alpha: 1.0,
      timestamp,
      maxAge: NEW_USER_FADE_DELAY + NEW_USER_FADE_TIME,
      transform: (item, age) => ({
        ...item,
        alpha: age < 100 ? item.alpha * age / 100 :
            age < NEW_USER_FADE_DELAY ? item.alpha :
                (1 - (age - NEW_USER_FADE_DELAY) / NEW_USER_FADE_TIME) * item.alpha
      }),
      hoverable: false,
      clickable: false
    });
    drawables.push({
      type: 'text',
      x: CANVAS_DEFAULT_WIDTH / 2,
      y: 25,
      z: 100,
      text: message,
      timestamp,
      maxAge: NEW_USER_FADE_DELAY + NEW_USER_FADE_TIME,
      fillColor: TEXT_FILL_COLOR,
      outlineColor: TEXT_OUTLINE_COLOR,
      fillAlpha: 1.0,
      outlineAlpha: 0.0,
      transform: (item, age) => ({
        ...item,
        y: age < 100 ? item.y * age / 100 : item.y,
        fillAlpha: age < 100 ? item.fillAlpha * age / 100 :
            age < NEW_USER_FADE_DELAY ? item.fillAlpha :
                (1 - (age - NEW_USER_FADE_DELAY) / NEW_USER_FADE_TIME) * item.fillAlpha
      }),
      hoverable: false,
      clickable: false
    });
  } else {
    // this is a regular edit event
    //console.debug("adding to drawables with color: " + color);

    let articleTitle = {
      // article title
      type: 'text',
      x, y,
      z: 50,
      timestamp,
      maxAge: TEXT_MAX_AGE,
      fillColor: TEXT_FILL_COLOR,
      outlineColor: TEXT_OUTLINE_COLOR,
      fillAlpha: silent ? SILENT_ALPHA : DEFAULT_ALPHA,
      outlineAlpha:  silent ? SILENT_ALPHA : DEFAULT_ALPHA,
      text: change.data.title,
      url: change.data.title_url,
      transform: (item, age) => ({
        ...item,
        fillAlpha: (age < 1000) ?item.fillAlpha : (1 - easeOutLinear((age - 1000) / (item.maxAge - 1000))) * item.fillAlpha,
        outlineAlpha: (age < 1000) ?item.fillAlpha : (1 - easeOutLinear((age - 1000) / (item.maxAge - 1000))) * item.outlineAlpha
      }),
      hoverable: false,
      clickable: true,
      onClick: null
    };
    articleTitle.onClick = () => {
      console.debug(`Clicked link for ${articleTitle.text} to go to ${articleTitle.url}`)
      window.open(articleTitle.url, '_blank');
    }

    let coloredCircle = {
      // colored circle
      type: 'circle',
      x, y,
      z: 50,
      r: scaledSize,
      timestamp,
      maxAge: CIRCLE_MAX_AGE,
      color,
      alpha: silent ? SILENT_ALPHA : DEFAULT_ALPHA,
      transform: (item, age) => ({
        ...item,
        alpha: (1 - easeOutSqrt(age / item.maxAge)) * item.alpha,
      }),
      hovering: false,
      hoverable: true,
      clickable: false,
      onHover: null,
      onHoverEnd: null,
      articleTitle: articleTitle,
      articleTitleTransform: null,
      articleTitleMaxAge: null
    };
    coloredCircle.onHover = () => {
      console.log(`Hovering over circle with title ${coloredCircle.articleTitle.text}`);
      coloredCircle.articleTitleTransform = coloredCircle.articleTitle.transform;
      coloredCircle.articleTitleMaxAge = coloredCircle.articleTitle.maxAge;
      coloredCircle.articleTitle.transform = (item, age) => ({...articleTitle})
      coloredCircle.articleTitle.maxAge = coloredCircle.maxAge;
      if (drawables.indexOf(articleTitle) === -1) {
        // it aged out of being drawn, so let's put it back
        drawables.push(articleTitle);
      }
    };
    coloredCircle.onHoverEnd = () => {
      console.log(`Ending hover over circle with title ${coloredCircle.articleTitle.text}`);
      coloredCircle.articleTitle.transform = coloredCircle.articleTitleTransform;
      coloredCircle.articleTitle.maxAge = coloredCircle.articleTitleMaxAge;
      coloredCircle.articleTitle.timestamp = Date.now() - 1000; // treat it as new but start fading right away.
    };

    let outerRing = {
      // outer ring
      type: 'ring',
      x, y,
      z: 50,
      rInner: scaledSize,
      rOuter: scaledSize + 20,
      timestamp,
      maxAge: RING_MAX_AGE,
      color: 'white',
      alpha: silent ? SILENT_ALPHA : 0.5,
      transform: (item, age) => ({
        ...item,
        alpha: (1 - easeOutSqrt(age / item.maxAge)) * item.alpha,
        rOuter: item.rOuter + 20 * easeOutSqrt(age / RING_MAX_AGE)
      }),
      hoverable: false,
      clickable: false
    };
    let flashOverlay = {
      // white circle flash overlay
      type: 'circle',
      x, y,
      z: 50,
      r: scaledSize,
      timestamp,
      maxAge: FLASH_MAX_AGE,
      color: 'white',
      alpha: 1.0,
      transform: (item, age) => ({
        ...item,
        alpha: (1 - easeOutSqrt( age / item.maxAge)) * item.alpha
      }),
      hoverable: false,
      clickable: false
    };
    drawables.push(coloredCircle);
    drawables.push(outerRing);
    drawables.push(flashOverlay);
    drawables.push(articleTitle);
  }
  rateMeasureQueue.enqueue(timestamp);
}

let resizeCanvasFn = null;

onMounted(() => {
  loadSounds();

  const canvas = document.createElement('canvas');
  canvasRef.value = canvas;
  document.getElementById('area').appendChild(canvas);
  ctx = canvas.getContext('2d');

  // we'll run this once then run it when the window size changes
  function resizeCanvas() {
    const container = canvas.parentElement;
    const rect = container.getBoundingClientRect();

    // sometimes the window resize event gets fired but the canvas container size hasn't actually changed, so we check
    if (rect.width === canvasWidth) {
      return;
    }

    canvasDpr = window.devicePixelRatio || 1;

    // Update width/height globals. these are CSS pixels
    canvasWidth = Math.floor(rect.width);
    canvasHeight = Math.floor(canvasWidth / canvasAspectRatio);

    // Resize canvas internal buffer for high density screens
    canvas.width = Math.floor(canvasWidth * canvasDpr);
    canvas.height = Math.floor(canvasHeight * canvasDpr);

    // Style it to fill the container
    canvas.style.width = `${canvasWidth}px`;
    canvas.style.height = `${canvasHeight}px`;

    // Scale the drawing context
    ctx.setTransform(1, 0, 0, 1, 0, 0); // reset any prior scaling
    ctx.scale(canvasDpr, canvasDpr);

    console.info(`Resized canvas to: (${canvasWidth}, ${canvasHeight}) * ${canvasDpr} dpr == (${canvas.width}, ${canvas.height})`);
  }

  resizeCanvasFn = resizeCanvas;

  // Initial resize
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Setup event handling
  watch(recentChange, (change) => {
    if (change) {
      handleRecentChange(change);
    }
  });

  // look for mouse movement
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width) / canvasDpr;
    const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height) / canvasDpr;

    for (let i = drawables.length - 1; i >= 0; i--) {
      const d = drawables[i];
      // let's only consider objects that want to listen to hover type events
      if (!d.hoverable) continue;
      let foundTarget = false;
      if (d.type === 'circle') {
        const dx = mouseX - d.x;
        const dy = mouseY - d.y;
        if (!foundTarget && dx * dx + dy * dy <= d.r * d.r) {
          if (!d.hovering) {
            d.hovering = true;
            d.onHover();
          }
          foundTarget = true;
        } else if (d.hovering) {
          d.hovering = false;
          d.onHoverEnd();
        }
      }
    }
  });

  // look for mouse clicks
  canvas.addEventListener('click', (e) => {
    console.debug('Heard a click, now locating it');
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width) / canvasDpr;
    const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height) / canvasDpr;

    for (let i = drawables.length - 1; i >= 0; i--) {
      const d = drawables[i];
      // let's only consider objects that want to listen to hover type events
      if (!d.clickable) continue;
      let foundTarget = false;
      if (d.type === 'text') {
        const tm = d.textMetrics;
        const lx = d.x - tm.actualBoundingBoxLeft;
        const rx = d.x + tm.actualBoundingBoxRight
        const ty = d.y - tm.actualBoundingBoxAscent;
        const by = d.y + tm.actualBoundingBoxRight;
        console.debug(`Checking bounds for text '${d.text}' x(${lx}..${rx}), y(${ty}..${by}) against mouse xy(${mouseX}, ${mouseY}`);
        if (!foundTarget && lx <= mouseX && mouseX <= rx &&
                            ty <= mouseY && mouseY <= by) {
          d.onClick();
          break;
        }
      }
    }
  });

  loop();
});


onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrameId);
  window.removeEventListener('resize', resizeCanvasFn);
});
</script>

<style scoped>
canvas {
  display: block;
}
</style>
