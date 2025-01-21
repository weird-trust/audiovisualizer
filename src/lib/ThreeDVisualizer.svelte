<script>
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

  let container;
  let audioContext;
  let analyser;
  let audioElement;
  let source;
  let dataArray;
  let sphereMesh;
  let geometry;
  let isPlaying = false;

  const initAudio = async () => {
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      dataArray = new Uint8Array(analyser.frequencyBinCount);

      audioElement = new Audio();
      audioElement.src = "audio/01-SAULT-4am.mp3";
      audioElement.loop = true;

      source = audioContext.createMediaElementSource(audioElement);
      source.connect(analyser);
      analyser.connect(audioContext.destination);

      await audioElement.play();
      isPlaying = true;
    } catch (error) {
      console.error("Error initializing audio:", error);
      isPlaying = false;
    }
  };

  onMount(() => {
    // Scene setup
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

    // Sphere setup
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

    // Animation function
    function animate() {
      requestAnimationFrame(animate);

      if (isPlaying && analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
        const positionAttribute = geometry.attributes.position;

        for (let i = 0; i < positionAttribute.count; i++) {
          const x = positionAttribute.getX(i);
          const y = positionAttribute.getY(i);
          const z = positionAttribute.getZ(i);
          const waveHeight = dataArray[i % dataArray.length] / 5000;
          const newZ = z + Math.sin(x * 2 + Date.now() * 0.01) * waveHeight * 2;
          positionAttribute.setZ(i, newZ);
        }
        positionAttribute.needsUpdate = true;
      }

      sphereMesh.rotation.x += 0.0015;
      sphereMesh.rotation.y += 0.0015;

      controls.update();
      renderer.render(scene, camera);
    }

    animate();

    // Window resize handler
    const onWindowResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener("resize", onWindowResize, false);

    return () => {
      window.removeEventListener("resize", onWindowResize);
      if (audioContext) {
        audioContext.close();
      }
    };
  });
</script>

<div bind:this={container}>
  {#if !isPlaying}
    <button class="start-button" on:click={initAudio}>
      Start Visualization
    </button>
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
</style>
