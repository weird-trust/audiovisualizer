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
  let isMobile = window.innerWidth < 768;
  let torusSize = isMobile ? 5 : 10;
  let torusThickness = isMobile ? 1.5 : 3;
  let cameraDistance = isMobile ? 15 : 25;

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

    geometry = new THREE.TorusGeometry(torusSize, torusThickness, 50, 25);

    const material = new THREE.MeshPhongMaterial({
      color: 0xff0000,
      wireframe: true,
      side: THREE.DoubleSide,
      emissive: 0xff0000,
      emissiveIntensity: 0.2
    });

    sphereMesh = new THREE.Mesh(geometry, material);
    sphereMesh.rotation.x = Math.PI / 2;
    scene.add(sphereMesh);

    camera.position.set(cameraDistance, 0, 0);
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
              (isMobile ? 2 : 3.5);
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
      isMobile = window.innerWidth < 768;
      torusSize = isMobile ? 5 : 10;
      torusThickness = isMobile ? 1.5 : 3;
      cameraDistance = isMobile ? 15 : 25;

      camera.aspect = window.innerWidth / window.innerHeight;
      camera.position.set(cameraDistance, 0, 0);
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

<style>
</style>
