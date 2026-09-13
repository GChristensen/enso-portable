// Background particle field: short glowing trails drifting along a flow field
// that swirls around the hero Enso circle.
(function () {
  "use strict";

  // ---- tuning ----
  var CONFIG = {
    count: 800,              // number of particles
    maxDpr: 2,               // cap on device pixel ratio (performance on hi-dpi screens)
    background: "#05070a",   // canvas clear color (should match page background)

    // appearance
    color: "52,232,138",     // trail color as "r,g,b"
    lineWidth: 1.65,         // trail thickness, px
    alphaBase: 0.05,         // trail opacity far from the swirl center
    alphaNearCenter: 0.28,   // extra opacity added near the swirl center
    glowFalloff: 300,        // px; how quickly the extra opacity fades with distance

    // motion
    segmentLength: 2.85,     // length of the stroke drawn each frame, px
    advanceFraction: 0.5,    // part of the segment a particle moves per frame (<1 makes trails overlap)
    timeStep: 0.0008,        // how fast the flow field evolves per frame
    lifeMin: 40,             // particle lifetime range, frames
    lifeMax: 220,
    offscreenMargin: 20,     // px beyond the edges before a particle respawns

    // flow field noise
    noiseFreq: 0.0032,       // spatial frequency of the main flow pattern
    noiseTimeY: 0.8,         // relative time speed of the vertical component
    noiseFreq2: 0.0018,      // spatial frequency of the diagonal secondary pattern
    noiseTime2: 0.5,         // relative time speed of the secondary pattern
    noiseAmp2: 0.8,          // strength of the secondary pattern, radians

    // swirl around the hero circle
    swirlX: 0.72,            // center x as a fraction of page width
    swirlY: 0.34,            // center y as a fraction of page height...
    swirlMaxY: 380,          // ...capped at this many px from the top
    swirlRadius: 320,        // px; how far the swirl reaches
    swirlStrength: 1.6       // how strongly particles orbit near the center
  };

  var canvas = document.getElementById("enso-field");
  if (!canvas) return;
  var context = canvas.getContext("2d");
  var container = canvas.parentElement;
  var pixelRatio = Math.min(window.devicePixelRatio || 1, CONFIG.maxDpr);
  var width = 0, height = 0;   // canvas size in CSS px (covers the whole page)
  var particles = [];
  var time = 0;                // flow field animation clock

  function randomBetween(min, max) { return min + Math.random() * (max - min); }

  function resize() {
    var newWidth = container.clientWidth;
    var newHeight = document.documentElement.scrollHeight;
    if (newWidth === width && newHeight === height) return;
    width = newWidth; height = newHeight;
    canvas.width = width * pixelRatio; canvas.height = height * pixelRatio;
    canvas.style.width = width + "px"; canvas.style.height = height + "px";
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    context.fillStyle = CONFIG.background;
    context.fillRect(0, 0, width, height);
  }

  function spawnParticle() {
    return {
      x: randomBetween(0, width),
      y: randomBetween(0, height),
      life: randomBetween(CONFIG.lifeMin, CONFIG.lifeMax)
    };
  }

  function seedParticles() {
    particles = [];
    for (var i = 0; i < CONFIG.count; i++) particles.push(spawnParticle());
  }

  function swirlCenter() {
    return { x: width * CONFIG.swirlX, y: Math.min(height * CONFIG.swirlY, CONFIG.swirlMaxY) };
  }

  // Flow direction (radians) at (x, y): animated noise blended with a vortex around the swirl center.
  function flowAngleAt(x, y, time, center) {
    var noiseAngle =
        Math.sin(x * CONFIG.noiseFreq + time) * Math.cos(y * CONFIG.noiseFreq - time * CONFIG.noiseTimeY) * Math.PI
      + Math.sin((x + y) * CONFIG.noiseFreq2 + time * CONFIG.noiseTime2) * CONFIG.noiseAmp2;

    var offsetX = x - center.x, offsetY = y - center.y;
    var distanceToCenter = Math.hypot(offsetX, offsetY);
    // 1 at the center, fading towards 0 with distance
    var swirlWeight = Math.exp(-distanceToCenter / CONFIG.swirlRadius);
    // perpendicular to the direction from the center, i.e. orbiting it
    var orbitAngle = Math.atan2(offsetY, offsetX) + Math.PI / 2;

    var blendedX = Math.cos(noiseAngle) * (1 - swirlWeight) + Math.cos(orbitAngle) * swirlWeight * CONFIG.swirlStrength;
    var blendedY = Math.sin(noiseAngle) * (1 - swirlWeight) + Math.sin(orbitAngle) * swirlWeight * CONFIG.swirlStrength;
    return Math.atan2(blendedY, blendedX);
  }

  function drawFrame() {
    time += CONFIG.timeStep;
    context.fillStyle = CONFIG.background;
    context.fillRect(0, 0, width, height);
    context.lineWidth = CONFIG.lineWidth;
    var center = swirlCenter();
    var advanceDistance = CONFIG.segmentLength * CONFIG.advanceFraction;
    var margin = CONFIG.offscreenMargin;

    for (var i = 0; i < particles.length; i++) {
      var particle = particles[i];
      var angle = flowAngleAt(particle.x, particle.y, time, center);
      var directionX = Math.cos(angle), directionY = Math.sin(angle);
      var segmentEndX = particle.x + directionX * CONFIG.segmentLength;
      var segmentEndY = particle.y + directionY * CONFIG.segmentLength;

      var distanceToCenter = Math.hypot(particle.x - center.x, particle.y - center.y);
      var centerProximity = Math.exp(-distanceToCenter / CONFIG.glowFalloff);
      var alpha = CONFIG.alphaBase + centerProximity * CONFIG.alphaNearCenter;
      context.strokeStyle = "rgba(" + CONFIG.color + "," + alpha.toFixed(3) + ")";

      context.beginPath();
      context.moveTo(particle.x, particle.y);
      context.lineTo(segmentEndX, segmentEndY);
      context.stroke();

      // advance only part of a segment so consecutive strokes overlap into a continuous trail
      particle.x += directionX * advanceDistance;
      particle.y += directionY * advanceDistance;
      particle.life--;

      var offscreen = particle.x < -margin || particle.x > width + margin
                   || particle.y < -margin || particle.y > height + margin;
      if (particle.life <= 0 || offscreen) {
        var replacement = spawnParticle();
        particle.x = replacement.x; particle.y = replacement.y; particle.life = replacement.life;
      }
    }
    requestAnimationFrame(drawFrame);
  }

  resize(); seedParticles(); drawFrame();
  window.addEventListener("resize", function () { resize(); seedParticles(); });
  if (window.ResizeObserver) new ResizeObserver(resize).observe(container);
})();
