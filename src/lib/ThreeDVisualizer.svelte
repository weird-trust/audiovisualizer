<script>
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

  let container;
  let dataArray = [];
  let sphereMesh;
  let geometry;
  let currentFrame = 0;
  let frameInterval;
  let showControls = false;
  let previousData = [];
  let initialPositions = [];
  let isMobile = window.innerWidth < 768;
  let spotifyUrl =
    "https://open.spotify.com/playlist/4yoqHUBDI7nR0Ca3XZW5rp?si=feb42eda2fa3467c";
  let imageUrl = "/unstable.png";

  // Audio-spezifische Variablen
  let audioContext;
  let analyser;
  let audioSource;
  let frequencyData;
  let audioFile;
  let isPlaying = false;
  let audioElement;
  let audioFileName = "Keine Datei ausgewählt";
  let visualizationType = "audio"; // 'audio' oder 'json'

  // Enhanced visualization parameters
  const params = {
    waveAmplitude: 0.3,
    waveSpeed: 0.008,
    waveDivisor: 15000,
    waveFrequency: 0.5,
    smoothingFactor: 0.5,
    bassBoost: 0.5,
    torusSize: isMobile ? 5 : 10,
    torusThickness: isMobile ? 1.5 : 3,
    cameraDistance: isMobile ? 15 : 25,
    fftSize: 1024 // Für Audio-Analyse, muss eine Potenz von 2 sein
  };

  function toggleControls() {
    showControls = !showControls;
  }

  async function loadFrequencyData() {
    try {
      const response = await fetch("/frequency_data.json");
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error loading frequency data:", error);
      return [];
    }
  }

  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
      if (file.type.startsWith("audio/")) {
        // Audio-Datei wurde hochgeladen
        handleAudioUpload(file);
      } else {
        // JSON-Datei mit Frequenzdaten wurde hochgeladen
        const reader = new FileReader();
        reader.onload = async (e) => {
          try {
            const data = JSON.parse(e.target.result);
            dataArray = data;
            visualizationType = "json";
            if (dataArray.length > 0) {
              if (frameInterval) clearInterval(frameInterval);
              frameInterval = setInterval(() => {
                currentFrame = (currentFrame + 1) % dataArray.length;
              }, 16);
            }
          } catch (error) {
            console.error("Error parsing uploaded file:", error);
          }
        };
        reader.readAsText(file);
      }
    }
  }

  function handleAudioUpload(file) {
    if (audioSource) {
      audioSource.disconnect();
    }

    audioFileName = file.name;
    audioFile = file;
    visualizationType = "audio";

    if (audioElement) {
      URL.revokeObjectURL(audioElement.src);
    }

    initAudio();
  }

  function initAudio() {
    if (!audioFile) return;

    // Erstelle Audio-Element
    if (!audioElement) {
      audioElement = new Audio();
    }

    // Audio-Kontext erstellen, wenn er noch nicht existiert
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    // Frequenzdaten-Array erstellen
    if (!analyser) {
      analyser = audioContext.createAnalyser();
      analyser.fftSize = params.fftSize;
      frequencyData = new Uint8Array(analyser.frequencyBinCount);
    } else {
      analyser.fftSize = params.fftSize;
      frequencyData = new Uint8Array(analyser.frequencyBinCount);
    }

    // Audio-Element-Quelle erstellen
    const fileURL = URL.createObjectURL(audioFile);
    audioElement.src = fileURL;
    audioElement.load();

    // Audio-Quelle mit Analyzer verbinden
    if (audioSource) {
      audioSource.disconnect();
    }

    audioSource = audioContext.createMediaElementSource(audioElement);
    audioSource.connect(analyser);
    analyser.connect(audioContext.destination);

    // Event-Listener für Audio-Ende
    audioElement.addEventListener("ended", () => {
      isPlaying = false;
    });
  }

  function toggleAudio() {
    if (!audioElement || !audioFile) return;

    if (audioContext.state === "suspended") {
      audioContext.resume();
    }

    if (isPlaying) {
      audioElement.pause();
      isPlaying = false;
    } else {
      audioElement.play();
      isPlaying = true;
    }
  }

  async function initVisualization() {
    if (visualizationType === "json") {
      dataArray = await loadFrequencyData();
      if (dataArray.length > 0) {
        if (frameInterval) clearInterval(frameInterval);
        frameInterval = setInterval(() => {
          currentFrame = (currentFrame + 1) % dataArray.length;
        }, 16);
      }
    }
  }

  onMount(async () => {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0xffffff, 1);
    container.appendChild(renderer.domElement);

    geometry = new THREE.TorusGeometry(
      params.torusSize,
      params.torusThickness,
      32,
      32
    );

    initialPositions = [...geometry.attributes.position.array];

    const material = new THREE.MeshPhongMaterial({
      color: 0x000000,
      wireframe: true,
      side: THREE.DoubleSide
    });

    sphereMesh = new THREE.Mesh(geometry, material);
    sphereMesh.rotation.x = Math.PI / 2;
    scene.add(sphereMesh);

    // Beleuchtung hinzufügen
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);

    camera.position.set(params.cameraDistance, 0, 0);
    camera.lookAt(0, 0, 0);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controls.enableZoom = true;

    await initVisualization();

    function animate() {
      requestAnimationFrame(animate);

      const positionAttribute = geometry.attributes.position;

      if (visualizationType === "audio" && analyser && isPlaying) {
        // Audio-Visualisierung
        analyser.getByteFrequencyData(frequencyData);

        // Daten normalisieren (0-255 zu 0-1)
        const normalizedData = Array.from(frequencyData).map(
          (val) => val / 255
        );

        for (let i = 0; i < positionAttribute.count; i++) {
          const x = positionAttribute.getX(i);
          const y = positionAttribute.getY(i);
          const z = initialPositions[i * 3 + 2]; // Original Z-Position

          // Frequenzband-Verarbeitung
          const frequencyIndex = i % normalizedData.length;
          const frequency =
            Math.pow(frequencyIndex / normalizedData.length, 2.5) *
            normalizedData.length;
          const dataIndex = Math.floor(frequency);

          // Glatte Übergänge zwischen Frames
          const currentValue = normalizedData[dataIndex] || 0;
          previousData[dataIndex] = previousData[dataIndex] || 0;
          const smoothedValue =
            currentValue * (1 - params.smoothingFactor) +
            previousData[dataIndex] * params.smoothingFactor;
          previousData[dataIndex] = smoothedValue;

          // Bass-Boost für niedrigere Frequenzen
          const bassBoostFactor =
            dataIndex < normalizedData.length / 4 ? params.bassBoost : 1;

          // Wellenhöhe mit Frequenzskalierung berechnen
          const waveHeight =
            smoothedValue *
            params.waveAmplitude *
            bassBoostFactor *
            (isMobile ? 2.5 : 4.0);

          const newZ =
            z +
            Math.sin(x * params.waveFrequency + Date.now() * params.waveSpeed) *
              waveHeight;

          positionAttribute.setZ(i, newZ);
        }
        positionAttribute.needsUpdate = true;
      } else if (visualizationType === "json" && dataArray.length > 0) {
        // JSON-Daten-Visualisierung (vorhandener Code)
        const currentData = dataArray[currentFrame];

        // Initialize previousData if needed
        if (previousData.length === 0) {
          previousData = [...currentData];
        }

        for (let i = 0; i < positionAttribute.count; i++) {
          const x = positionAttribute.getX(i);
          const y = positionAttribute.getY(i);
          const z = positionAttribute.getZ(i);

          // Frequency band processing
          const frequencyIndex = i % currentData.length;
          const frequency =
            Math.pow(frequencyIndex / currentData.length, 2.5) *
            currentData.length;
          const dataIndex = Math.floor(frequency);

          // Smooth transition between frames
          const currentValue = currentData[dataIndex] || 0;
          previousData[dataIndex] = previousData[dataIndex] || 0;
          const smoothedValue =
            currentValue * (1 - params.smoothingFactor) +
            previousData[dataIndex] * params.smoothingFactor;
          previousData[dataIndex] = smoothedValue;

          // Apply bass boost to lower frequencies
          const bassBoostFactor =
            dataIndex < currentData.length / 4 ? params.bassBoost : 1;

          // Calculate wave height with frequency scaling
          const waveHeight =
            Math.log(1 + smoothedValue / params.waveDivisor) *
            params.waveAmplitude *
            bassBoostFactor;

          const newZ =
            z +
            Math.sin(x * params.waveFrequency + Date.now() * params.waveSpeed) *
              waveHeight *
              (isMobile ? 2.5 : 4.0);

          positionAttribute.setZ(i, newZ);
        }
        positionAttribute.needsUpdate = true;
      }

      sphereMesh.rotation.z += 0.0002;
      controls.update();
      renderer.render(scene, camera);
    }

    animate();

    const onWindowResize = () => {
      isMobile = window.innerWidth < 768;
      params.torusSize = isMobile ? 5 : 10;
      params.torusThickness = isMobile ? 1.5 : 3;
      params.cameraDistance = isMobile ? 15 : 25;

      camera.aspect = window.innerWidth / window.innerHeight;
      camera.position.set(params.cameraDistance, 0, 0);
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener("resize", onWindowResize, false);

    return () => {
      window.removeEventListener("resize", onWindowResize);
      if (frameInterval) clearInterval(frameInterval);
      if (audioElement) {
        audioElement.pause();
        audioElement.src = "";
      }
      if (audioContext) {
        audioContext.close();
      }
    };
  });
</script>

<svelte:head>
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
  />
</svelte:head>

<div class="canvas-container" bind:this={container}></div>

<button class="toggle-controls" on:click={toggleControls}>
  {showControls ? "✕" : "⚙️"}
</button>

{#if showControls}
  <div class="controls-panel">
    <div class="control-group">
      <h3>Audiodatei hochladen</h3>
      <div class="control-row">
        <input
          type="file"
          accept="audio/*,.json"
          on:change={handleFileUpload}
        />
      </div>
      {#if audioFileName}
        <div class="filename">{audioFileName}</div>
      {/if}
    </div>

    {#if visualizationType === "audio" && audioFile}
      <div class="control-group">
        <div class="audio-controls">
          <button class="audio-button" on:click={toggleAudio}>
            {isPlaying ? "Pause" : "Play"}
          </button>
        </div>
      </div>

      <div class="control-group">
        <label>
          FFT Size (Frequenzauflösung)
          <div class="control-row">
            <select
              bind:value={params.fftSize}
              on:change={() => {
                if (analyser) {
                  analyser.fftSize = params.fftSize;
                  frequencyData = new Uint8Array(analyser.frequencyBinCount);
                }
              }}
            >
              <option value={256}>256</option>
              <option value={512}>512</option>
              <option value={1024}>1024</option>
              <option value={2048}>2048</option>
              <option value={4096}>4096</option>
              <option value={8192}>8192</option>
            </select>
          </div>
        </label>
      </div>
    {/if}

    <hr />

    <div class="control-group">
      <label>
        Wave Amplitude
        <div class="control-row">
          <input
            type="range"
            bind:value={params.waveAmplitude}
            min="0"
            max="1"
            step="0.1"
          />
          <span>{params.waveAmplitude}</span>
        </div>
      </label>
    </div>

    <div class="control-group">
      <label>
        Wave Speed
        <div class="control-row">
          <input
            type="range"
            bind:value={params.waveSpeed}
            min="0"
            max="0.02"
            step="0.001"
          />
          <span>{params.waveSpeed}</span>
        </div>
      </label>
    </div>

    {#if visualizationType === "json"}
      <div class="control-group">
        <label>
          Wave Divisor
          <div class="control-row">
            <input
              type="range"
              bind:value={params.waveDivisor}
              min="5000"
              max="25000"
              step="1000"
            />
            <span>{params.waveDivisor}</span>
          </div>
        </label>
      </div>
    {/if}

    <div class="control-group">
      <label>
        Wave Frequency
        <div class="control-row">
          <input
            type="range"
            bind:value={params.waveFrequency}
            min="0"
            max="2"
            step="0.1"
          />
          <span>{params.waveFrequency}</span>
        </div>
      </label>
    </div>

    <div class="control-group">
      <label>
        Smoothing Factor
        <div class="control-row">
          <input
            type="range"
            bind:value={params.smoothingFactor}
            min="0"
            max="1"
            step="0.1"
          />
          <span>{params.smoothingFactor}</span>
        </div>
      </label>
    </div>

    <div class="control-group">
      <label>
        Bass Boost
        <div class="control-row">
          <input
            type="range"
            bind:value={params.bassBoost}
            min="1"
            max="4"
            step="0.1"
          />
          <span>{params.bassBoost}</span>
        </div>
      </label>
    </div>
  </div>
{/if}

<a
  href={spotifyUrl}
  target="_blank"
  rel="noopener noreferrer"
  class="spotify-link"
>
  <img src={imageUrl} alt="Spotify" draggable="false" />
</a>

<style>
  /* div {
    width: 100vw;
    height: 100vh;
    margin: 0;
    padding: 0;
    overflow: hidden;
    position: fixed;
    top: 0;
    left: 0;
  } */

  .spotify-link {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1000;
    transition: transform 0.3s ease;
    user-select: none;
    text-decoration: none;
    color: transparent;
    cursor: pointer;
  }

  .spotify-link img {
    width: 50vw;
    height: auto;
    pointer-events: none;
    -webkit-user-drag: none;
    user-select: none;
    -moz-user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
    display: block;
  }

  .spotify-link:hover {
    transform: translate(-50%, -50%) scale(1.1);
  }

  @media (max-width: 768px) {
    .spotify-link img {
      width: 70vw;
    }
  }

  .canvas-container {
    width: 100vw;
    height: 100vh;
    margin: 0;
    padding: 0;
    overflow: hidden;
    position: fixed;
    top: 0;
    left: 0;
  }

  .toggle-controls {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1001;
    padding: 12px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .controls-panel {
    position: fixed;
    top: 80px;
    right: 20px;
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    width: 300px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    max-height: 80vh;
    overflow-y: auto;
  }

  .control-group {
    width: 100%;
    margin-bottom: 15px;
  }

  .control-group h3 {
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 16px;
  }

  .control-group label {
    display: flex;
    flex-direction: column;
    font-size: 14px;
    color: #333;
    margin-bottom: 4px;
  }

  .control-row {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  .control-row input[type="range"] {
    flex: 1;
    min-width: 0;
  }

  .control-row input[type="file"] {
    width: 100%;
  }

  .control-row span {
    min-width: 45px;
    text-align: right;
    font-family: monospace;
  }

  .filename {
    font-size: 12px;
    color: #666;
    margin-top: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .audio-controls {
    display: flex;
    justify-content: center;
    margin-top: 10px;
  }

  .audio-button {
    padding: 8px 16px;
    background-color: #000;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background-color 0.2s;
  }

  .audio-button:hover {
    background-color: #333;
  }

  hr {
    border: none;
    border-top: 1px solid #eee;
    margin: 10px 0;
  }

  @media (max-width: 768px) {
    .controls-panel {
      top: auto;
      bottom: 80px;
      right: 10px;
      width: calc(100vw - 60px);
      max-width: 300px;
      max-height: 60vh;
    }
  }

  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
  }
</style>
