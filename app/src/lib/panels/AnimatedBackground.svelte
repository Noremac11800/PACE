<script lang="ts">
  import { onMount } from "svelte";

  interface Node {
    x: number;
    y: number;
    vx: number;
    vy: number;
    size: number;
  }

  const nodeCount = 25;
  const connectionDistance = 120;
  const nodes: Node[] = $state([]);

  // Initialize nodes with random positions and velocities
  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      x: Math.random() * 100,
      y: Math.random() * 100,
      vx: (Math.random() - 0.5) * 0.03,
      vy: (Math.random() - 0.5) * 0.03,
      size: Math.random() * 3 + 4,
    });
  }

  // Animation loop
  let animationId: number;

  function animate() {
    nodes.forEach((node) => {
      node.x += node.vx;
      node.y += node.vy;

      // Bounce off edges
      if (node.x <= 0 || node.x >= 100) node.vx *= -1;
      if (node.y <= 0 || node.y >= 100) node.vy *= -1;

      // Keep within bounds
      node.x = Math.max(0, Math.min(100, node.x));
      node.y = Math.max(0, Math.min(100, node.y));
    });

    animationId = requestAnimationFrame(animate);
  }

  onMount(() => {
    animate();
    return () => cancelAnimationFrame(animationId);
  });

  function getDistance(n1: Node, n2: Node): number {
    const dx = n1.x - n2.x;
    const dy = n1.y - n2.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function getOpacity(distance: number): number {
    return Math.max(0, 1 - distance / (connectionDistance / 5)) * 0.6;
  }
</script>

<div class="absolute inset-0 overflow-hidden pointer-events-none">
  <!-- Gradient overlay for depth -->
  <div
    class="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-secondary-500/5"
  ></div>

  <!-- SVG for connections -->
  <svg class="absolute inset-0 w-full h-full" preserveAspectRatio="none">
    {#each nodes as node, i (i)}
      {#each nodes.slice(i + 1) as otherNode, j (j)}
        {@const distance = getDistance(node, otherNode)}
        {#if distance < connectionDistance / 5}
          {@const opacity = getOpacity(distance)}
          <line
            x1="{node.x}%"
            y1="{node.y}%"
            x2="{otherNode.x}%"
            y2="{otherNode.y}%"
            stroke="currentColor"
            stroke-width="1.5"
            class="text-primary-500"
            style="opacity: {opacity}"
          />
        {/if}
      {/each}
    {/each}
  </svg>

  <!-- Nodes -->
  {#each nodes as node, i (i)}
    <div
      class="absolute rounded-full bg-primary-500/40 backdrop-blur-sm shadow-[0_0_10px_currentColor]"
      style="
        left: {node.x}%;
        top: {node.y}%;
        width: {node.size}px;
        height: {node.size}px;
        transform: translate(-50%, -50%);
      "
    ></div>
  {/each}
</div>

<style>
  /* Gentle pulse animation for nodes */
  div > div:last-child {
    animation: pulse 4s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 0.4;
      transform: translate(-50%, -50%) scale(1);
    }
    50% {
      opacity: 0.8;
      transform: translate(-50%, -50%) scale(1.2);
    }
  }
</style>
