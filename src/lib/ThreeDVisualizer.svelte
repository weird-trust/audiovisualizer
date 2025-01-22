<script>
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

  let container;
  let dataArray = [];
  let sphereMesh;
  let geometry;
  let isPlaying = false;
  let currentFrame = 0;
  let frameInterval;
  let waveAmplitude = 0.1; // Reduced from 0.3
  let waveSpeed = 0.001; // Reduced from 0.005
  let waveDivisor = 51200; // Doubled from 25600
  let waveFrequency = 0.5; // Reduced from 1

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
      isPlaying = true;
      frameInterval = setInterval(() => {
        currentFrame = (currentFrame + 1) % dataArray.length;
      }, 100);
    }
  }

  onMount(() => {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0xffffff, 1);
    container.appendChild(renderer.domElement);

    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(0, 1, 1).normalize();
    scene.add(light);

    geometry = new THREE.SphereGeometry(5, 64, 64);
    const material = new THREE.MeshPhongMaterial({
      color: 0x000aa,
      side: THREE.DoubleSide,
      wireframe: true
    });
    sphereMesh = new THREE.Mesh(geometry, material);
    scene.add(sphereMesh);

    camera.position.z = 15;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controls.enableZoom = true;

    function animate() {
      requestAnimationFrame(animate);

      if (isPlaying && dataArray.length > 0) {
        const positionAttribute = geometry.attributes.position;
        const currentData = dataArray[currentFrame];

        for (let i = 0; i < positionAttribute.count; i++) {
          const x = positionAttribute.getX(i);
          const y = positionAttribute.getY(i);
          const z = positionAttribute.getZ(i);
          // Scaled wave calculation
          const waveHeight =
            (currentData[i % currentData.length] / waveDivisor) * waveAmplitude;
          const newZ =
            z +
            Math.sin(x * waveFrequency + Date.now() * waveSpeed) *
              waveHeight *
              0.5;
          positionAttribute.setZ(i, newZ);
        }
        positionAttribute.needsUpdate = true;
      }

      sphereMesh.rotation.x += 0.001;
      sphereMesh.rotation.y += 0.001;

      controls.update();
      renderer.render(scene, camera);
    }

    animate();

    const onWindowResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
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

<div bind:this={container}>
  {#if !isPlaying}
    <button class="start-button" on:click={initVisualization}>
      Start Visualization
    </button>
  {:else}
    <div class="controls">
      <label>
        Wave Height
        <input
          type="range"
          min="0"
          max="0.5"
          step="0.01"
          bind:value={waveAmplitude}
        />
      </label>
      <label>
        Wave Speed
        <input
          type="range"
          min="0.0001"
          max="0.002"
          step="0.0001"
          bind:value={waveSpeed}
        />
      </label>
      <label>
        Wave Frequency
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.1"
          bind:value={waveFrequency}
        />
      </label>
    </div>
  {/if}
</div>

<style>
  .start-button {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    padding: 1rem 2rem;
    font-size: 1.2rem;
    background: blue;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    z-index: 1000;
  }

  .start-button:hover {
    background: rgba(0, 0, 255, 0.483);
  }

  .controls {
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.7);
    padding: 1rem;
    border-radius: 8px;
    color: white;
    z-index: 1000;
  }

  .controls label {
    display: block;
    margin: 10px 0;
  }

  .controls input {
    width: 100%;
    margin-top: 5px;
  }
</style>
