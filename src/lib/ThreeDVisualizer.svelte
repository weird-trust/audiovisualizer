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
  let previousData = [];
  let initialPositions = [];
  let isMobile = window.innerWidth < 768;
  let spotifyUrl =
    "https://open.spotify.com/playlist/4yoqHUBDI7nR0Ca3XZW5rp?si=feb42eda2fa3467c";
  let imageUrl = "/unstable.png";

  // Enhanced visualization parameters
  const params = {
    waveAmplitude: 0.3,
    waveSpeed: 0.008,
    waveDivisor: 15000,
    waveFrequency: 0.5,
    smoothingFactor: 0.3,
    bassBoost: 1.5,
    torusSize: isMobile ? 5 : 10,
    torusThickness: isMobile ? 1.5 : 3,
    cameraDistance: isMobile ? 15 : 25
  };

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

  async function initVisualization() {
    dataArray = await loadFrequencyData();
    if (dataArray.length > 0) {
      frameInterval = setInterval(() => {
        currentFrame = (currentFrame + 1) % dataArray.length;
      }, 16);
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

    camera.position.set(params.cameraDistance, 0, 0);
    camera.lookAt(0, 0, 0);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controls.enableZoom = true;

    await initVisualization();

    function animate() {
      requestAnimationFrame(animate);

      if (dataArray.length > 0) {
        const positionAttribute = geometry.attributes.position;
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
            Math.pow(frequencyIndex / currentData.length, 1.5) *
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
    };
  });
</script>

<svelte:head>
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
  />
</svelte:head>

<div bind:this={container}></div>

<a
  href={spotifyUrl}
  target="_blank"
  rel="noopener noreferrer"
  class="spotify-link"
>
  <img src={imageUrl} alt="Spotify" draggable="false" />
</a>

<style>
  div {
    width: 100vw;
    height: 100vh;
    margin: 0;
    padding: 0;
    overflow: hidden;
    position: fixed;
    top: 0;
    left: 0;
  }

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

  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
  }
</style>
