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

  // Aufzeichnungs-Variablen
  let isRecording = false;
  let recordedData = [];
  let recordStartTime = 0;
  let recordingInterval = 3; // Nur jeden 3. Frame aufzeichnen (für kleinere Dateien)

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
    fftSize: 1024, // Für Audio-Analyse, muss eine Potenz von 2 sein
    geometryType: "torus" // Standard-Geometrie
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

  // Funktion zum Wechseln der Geometrie
  function changeGeometry(geometryType) {
    if (!sphereMesh) return;

    // Parameter für jede Geometrie
    const geometryParams = {
      torus: {
        geometry: new THREE.TorusGeometry(
          params.torusSize,
          params.torusThickness,
          32,
          32
        ),
        scale: 1,
        rotationX: Math.PI / 2
      },
      sphere: {
        geometry: new THREE.SphereGeometry(params.torusSize, 32, 32),
        scale: 1,
        rotationX: 0
      },
      box: {
        geometry: new THREE.BoxGeometry(
          params.torusSize * 1.5,
          params.torusSize * 1.5,
          params.torusSize * 1.5,
          10,
          10,
          10
        ),
        scale: 1,
        rotationX: 0
      },
      cylinder: {
        geometry: new THREE.CylinderGeometry(
          params.torusSize / 1.5,
          params.torusSize / 1.5,
          params.torusSize * 2,
          32,
          32
        ),
        scale: 1,
        rotationX: Math.PI / 2
      },
      cone: {
        geometry: new THREE.ConeGeometry(
          params.torusSize,
          params.torusSize * 2,
          32,
          32
        ),
        scale: 1,
        rotationX: Math.PI
      },
      torusKnot: {
        geometry: new THREE.TorusKnotGeometry(
          params.torusSize / 1.5,
          params.torusThickness / 1.5,
          100,
          16
        ),
        scale: 1,
        rotationX: Math.PI / 2
      },
      icosahedron: {
        geometry: new THREE.IcosahedronGeometry(params.torusSize, 1),
        scale: 1,
        rotationX: 0
      },
      plane: {
        geometry: new THREE.PlaneGeometry(
          params.torusSize * 3,
          params.torusSize * 3,
          32,
          32
        ),
        scale: 1,
        rotationX: Math.PI / 2
      }
    };

    // Wenn die gewählte Geometrie existiert
    if (geometryParams[geometryType]) {
      // Alte Geometrie speichern und löschen
      if (geometry) {
        geometry.dispose();
      }

      // Neue Geometrie erstellen
      geometry = geometryParams[geometryType].geometry;
      initialPositions = [...geometry.attributes.position.array];

      // Material beibehalten
      const material = sphereMesh.material;

      // Altes Mesh aus der Szene entfernen
      const scene = sphereMesh.parent;
      scene.remove(sphereMesh);

      // Neues Mesh erstellen
      sphereMesh = new THREE.Mesh(geometry, material);
      sphereMesh.rotation.x = geometryParams[geometryType].rotationX;
      sphereMesh.scale.set(
        geometryParams[geometryType].scale,
        geometryParams[geometryType].scale,
        geometryParams[geometryType].scale
      );

      // Neues Mesh zur Szene hinzufügen
      scene.add(sphereMesh);

      // Geometrietyp in Parametern speichern
      params.geometryType = geometryType;
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
            const parsedData = JSON.parse(e.target.result);

            // Prüfe, ob es das neue Format mit Metadaten ist
            if (parsedData.frames && Array.isArray(parsedData.frames)) {
              dataArray = parsedData.frames;

              // Zeige Metadaten an, wenn vorhanden
              if (parsedData.metadata) {
                console.log("Geladene Metadaten:", parsedData.metadata);
                audioFileName =
                  parsedData.metadata.originalFile || "Unbekannte Datei";
              }
            }
            // Kompatibilität mit dem alten Format (reine Array-Struktur)
            else if (Array.isArray(parsedData)) {
              dataArray = parsedData;
            } else {
              throw new Error("Unbekanntes Datenformat");
            }

            visualizationType = "json";
            if (dataArray.length > 0) {
              if (frameInterval) clearInterval(frameInterval);
              frameInterval = setInterval(() => {
                currentFrame = (currentFrame + 1) % dataArray.length;
              }, 16);
            }
          } catch (error) {
            console.error("Error parsing uploaded file:", error);
            alert("Fehler beim Laden der Datei: " + error.message);
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

      // Wenn wir aufnehmen, stoppen wir auch die Aufnahme
      if (isRecording) {
        stopRecording();
      }
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

      // Wenn wir aufnehmen, stoppen wir auch die Aufnahme
      if (isRecording) {
        stopRecording();
      }
    } else {
      audioElement.play();
      isPlaying = true;
    }
  }

  // Funktion zum Starten der Aufzeichnung
  function startRecording() {
    if (!isPlaying || !analyser) return;

    recordedData = [];
    isRecording = true;
    recordStartTime = Date.now();

    // Setze vorherige Daten zurück
    previousData = [];
  }

  // Funktion zum Stoppen der Aufzeichnung
  function stopRecording() {
    isRecording = false;
  }

  // Funktion zum Aufzeichnen eines Frames
  function recordFrame() {
    if (!isRecording || !analyser || !frequencyData) return;

    // Reduziere die Aufnahmefrequenz für kleinere Dateien
    if (recordedData.length % recordingInterval !== 0) {
      return;
    }

    // Kopiere die aktuellen Frequenzdaten und reduziere Genauigkeit
    const frameData = Array.from(frequencyData).map((val) => {
      // Normalisieren (0-255 zu 0-1) und auf 2 Dezimalstellen runden
      return Math.round((val / 255) * 100) / 100;
    });

    recordedData.push(frameData);
  }

  // Funktion zum Herunterladen der aufgezeichneten Daten
  function downloadRecordedData() {
    if (recordedData.length === 0) {
      alert(
        "Keine Daten zum Herunterladen verfügbar. Bitte zuerst aufzeichnen."
      );
      return;
    }

    // Erstelle ein Metadaten-Objekt
    const metadata = {
      originalFile: audioFileName,
      recordingDate: new Date().toISOString(),
      fftSize: params.fftSize,
      frameCount: recordedData.length,
      frameInterval: recordingInterval,
      duration: (Date.now() - recordStartTime) / 1000,
      params: { ...params }
    };

    // Kombiniere Metadaten und Frames
    const exportData = {
      metadata: metadata,
      frames: recordedData
    };

    // Erstelle einen Blob mit den JSON-Daten
    const dataBlob = new Blob([JSON.stringify(exportData)], {
      type: "application/json"
    });

    // Erstelle einen Download-Link
    const url = URL.createObjectURL(dataBlob);
    const a = document.createElement("a");
    a.href = url;

    // Verwende den Dateinamen der Audiodatei, aber mit .json-Endung
    const baseName = audioFileName.split(".").slice(0, -1).join(".");
    a.download = `${baseName || "frequency-data"}.json`;

    // Füge den Link zum DOM hinzu, klicke ihn an und entferne ihn wieder
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Bereinige die URL
    URL.revokeObjectURL(url);
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

    // Anfängliche Geometrie basierend auf params.geometryType erstellen
    switch (params.geometryType) {
      case "torus":
        geometry = new THREE.TorusGeometry(
          params.torusSize,
          params.torusThickness,
          32,
          32
        );
        break;
      default:
        geometry = new THREE.TorusGeometry(
          params.torusSize,
          params.torusThickness,
          32,
          32
        );
    }

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

        // Wenn wir aufzeichnen, speichere den aktuellen Frame
        if (isRecording) {
          recordFrame();
        }

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
          const z = initialPositions[i * 3 + 2]; // Original Z-Position

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
          // Anpassung, um sowohl mit altem als auch neuem Format zu funktionieren
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

      <div class="control-group">
        <h3>Frequenzdaten speichern</h3>
        <div class="record-controls">
          <div class="control-row">
            <label>
              Aufnahme-Intervall:
              <select bind:value={recordingInterval}>
                <option value={1}>Jeden Frame (groß)</option>
                <option value={2}>Jeden 2. Frame</option>
                <option value={3}>Jeden 3. Frame (Standard)</option>
                <option value={4}>Jeden 4. Frame</option>
                <option value={6}>Jeden 6. Frame (klein)</option>
              </select>
            </label>
          </div>

          {#if !isRecording}
            <button
              class="record-button"
              on:click={startRecording}
              disabled={!isPlaying}
            >
              Aufzeichnen starten
            </button>
          {:else}
            <button class="record-button recording" on:click={stopRecording}>
              Aufzeichnung stoppen ({Math.floor(
                (Date.now() - recordStartTime) / 1000
              )}s)
            </button>
          {/if}

          <button
            class="download-button"
            on:click={downloadRecordedData}
            disabled={recordedData.length === 0}
          >
            Frequenzdaten herunterladen ({recordedData.length} Frames)
          </button>
        </div>

        {#if recordedData.length > 0}
          <div class="info-text">
            {recordedData.length} Frames aufgezeichnet ({(
              (recordedData.length / 60) *
              recordingInterval
            ).toFixed(1)} Sekunden bei 60 FPS)<br />
            Geschätzte Dateigröße: ~{Math.round(
              (recordedData.length * frequencyData.length * 4) / 1024
            )} KB
          </div>
        {/if}
      </div>
    {/if}

    <hr />

    <div class="control-group">
      <h3>Visualisierung</h3>
      <label>
        Geometrie
        <div class="control-row">
          <select
            bind:value={params.geometryType}
            on:change={() => changeGeometry(params.geometryType)}
          >
            <option value="torus">Torus (Ring)</option>
            <option value="sphere">Kugel</option>
            <option value="box">Würfel</option>
            <option value="cylinder">Zylinder</option>
            <option value="cone">Kegel</option>
            <option value="torusKnot">Torusknoten</option>
            <option value="icosahedron">Ikosaeder</option>
            <option value="plane">Ebene</option>
          </select>
        </div>
      </label>
    </div>

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

  .record-controls {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 10px;
  }

  .record-button,
  .download-button {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background-color 0.2s;
  }

  .record-button {
    background-color: #f44336;
    color: white;
  }

  .record-button:hover:not(:disabled) {
    background-color: #d32f2f;
  }

  .record-button.recording {
    background-color: #d32f2f;
    animation: pulse 1.5s infinite;
  }

  .download-button {
    background-color: #4caf50;
    color: white;
  }

  .download-button:hover:not(:disabled) {
    background-color: #388e3c;
  }

  .record-button:disabled,
  .download-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }

  .info-text {
    font-size: 12px;
    color: #666;
    margin-top: 8px;
  }

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
    100% {
      opacity: 1;
    }
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
