<script>
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

  let container;

  onMount(() => {
    // Szene, Kamera und Renderer erstellen
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0xffffff, 1); // Hintergrundfarbe des Renderers auf Weiß setzen
    container.appendChild(renderer.domElement);

    // Licht hinzufügen
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(0, 1, 1).normalize();
    scene.add(light);

    // Benutzerdefinierte Geometrie für die Kugel erstellen
    const radius = 5;
    const widthSegments = 64;
    const heightSegments = 64;
    const geometry = new THREE.SphereGeometry(
      radius,
      widthSegments,
      heightSegments
    );

    // Material für das Mesh erstellen
    const material = new THREE.MeshPhongMaterial({
      color: 0x000aa,
      side: THREE.DoubleSide,
      wireframe: true
    });
    const sphereMesh = new THREE.Mesh(geometry, material);
    scene.add(sphereMesh);

    camera.position.z = 15;

    // OrbitControls hinzufügen
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controls.enableZoom = true;

    // Audio-Setup
    const audioContext = new (window.AudioContext ||
      window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    // Audioquelle erstellen (z.B. ein stummes Audioelement)
    const audioElement = new Audio();
    audioElement.src = "src/assets/01-SAULT-4am.mp3"; // Pfad zur Audio-Datei
    audioElement.loop = true;
    audioElement.volume = 0;
    audioElement.play();

    const source = audioContext.createMediaElementSource(audioElement);
    source.connect(analyser);
    analyser.connect(audioContext.destination);

    // Animationsfunktion
    function animate() {
      requestAnimationFrame(animate);

      analyser.getByteFrequencyData(dataArray);

      // Vertices der Geometrie basierend auf den Audiodaten animieren
      const positionAttribute = geometry.attributes.position;
      for (let i = 0; i < positionAttribute.count; i++) {
        const x = positionAttribute.getX(i);
        const y = positionAttribute.getY(i);
        const z = positionAttribute.getZ(i);

        // Verstärkte Wellenbewegung basierend auf Audiodaten
        const waveHeight = dataArray[i % dataArray.length] / 5000;
        const newZ = z + Math.sin(x * 2 + Date.now() * 0.01) * waveHeight * 2;

        positionAttribute.setZ(i, newZ);
      }
      positionAttribute.needsUpdate = true;

      // Standardmäßige Rotation des Meshes
      sphereMesh.rotation.x += 0.0015;
      sphereMesh.rotation.y += 0.0015;

      controls.update();

      renderer.render(scene, camera);
    }

    animate();

    // Fenstergröße überwachen und Renderer anpassen
    window.addEventListener("resize", onWindowResize, false);

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }
  });
</script>

<div bind:this={container} style="width: 100vw; height: 100vh;"></div>

<style>
  div {
    display: block;
  }
</style>
