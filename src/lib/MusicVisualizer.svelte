<script>
  import { onMount } from "svelte";

  let canvas;
  let ctx;

  onMount(() => {
    ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    visualize();
  });

  function visualize() {
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = 10;
      let barHeight;
      let x = 0;

      for (let i = 0; i < 50; i++) {
        barHeight = Math.random() * 100;
        ctx.fillStyle = `rgb(${barHeight + 100},50,50)`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }

      requestAnimationFrame(draw);
    }
    draw();
  }
</script>

<canvas bind:this={canvas}></canvas>

<style>
  canvas {
    display: block;
    width: 100vw;
    height: 100vh;
  }
</style>
