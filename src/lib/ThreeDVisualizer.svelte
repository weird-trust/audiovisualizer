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
  let waveAmplitude = 0.1;
  let waveSpeed = 0.001;
  let waveDivisor = 51200;
  let waveFrequency = 0.5;

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
      }, 100);
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
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0xffffff, 1);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(1, 1, 0).normalize();
    scene.add(light);

    geometry = new THREE.TorusGeometry(10, 3, 50, 250);
    // geometry = new THREE.PlaneGeometry(25, 25, 50, 50);

    const material = new THREE.MeshPhongMaterial({
      color: 0xff0000,
      wireframe: true,
      side: THREE.DoubleSide, // Enable double-sided rendering
      emissive: 0xff0000, // Add emissive color
      emissiveIntensity: 0.2
    });
    sphereMesh = new THREE.Mesh(geometry, material);
    sphereMesh.rotation.x = Math.PI / 2;
    scene.add(sphereMesh);

    camera.position.set(25, 0, 0);
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

        for (let i = 0; i < positionAttribute.count; i++) {
          const x = positionAttribute.getX(i);
          const y = positionAttribute.getY(i);
          const z = positionAttribute.getZ(i);
          const waveHeight =
            (currentData[i % currentData.length] / waveDivisor) * waveAmplitude;
          const newZ =
            z +
            Math.sin(x * waveFrequency + Date.now() * waveSpeed) *
              waveHeight *
              3.5;
          positionAttribute.setZ(i, newZ);
        }
        positionAttribute.needsUpdate = true;
      }

      sphereMesh.rotation.z += 0.0009;

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
</div>

<style>
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

  label {
    display: block;
    margin: 10px 0;
  }

  input {
    width: 100%;
    margin-top: 5px;
  }
</style>
