<script lang="ts">
  let {
    consoleOutput,
    consoleRef = $bindable(),
  }: {
    consoleOutput: string[];
    consoleRef?: HTMLDivElement;
  } = $props();

  // ANSI color codes to HTML converter
  function ansiToHtml(text: string): string {
    const ansiColors: Record<string, string> = {
      "30": "color: #000000;",
      "31": "color: #ef4444;",
      "32": "color: #22c55e;",
      "33": "color: #eab308;",
      "34": "color: #3b82f6;",
      "35": "color: #a855f7;",
      "36": "color: #06b6d4;",
      "37": "color: #e5e7eb;",
      "90": "color: #6b7280;",
      "91": "color: #f87171;",
      "92": "color: #4ade80;",
      "93": "color: #facc15;",
      "94": "color: #60a5fa;",
      "95": "color: #c084fc;",
      "96": "color: #22d3ee;",
      "97": "color: #f3f4f6;",
    };

    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br>");

    // Handle ANSI codes
    html = html.replace(/\x1b\[(\d+)(;\d+)*m/g, (match, ...groups) => {
      const codes = groups[0].split(";");
      const colorCode = codes.find((c: string) => ansiColors[c]);
      if (colorCode) {
        return `</span><span style="${ansiColors[colorCode]}">`;
      }
      if (codes.includes("0")) {
        return "</span><span>";
      }
      if (codes.includes("1")) {
        return '</span><span style="font-weight: bold;">';
      }
      return "";
    });

    return `<span>${html}</span>`;
  }
</script>

<div
  bind:this={consoleRef}
  class="flex-1 overflow-auto p-4 font-mono text-sm bg-surface-50-950 cursor-text"
>
  {#each consoleOutput as line, i (i)}
    <div class="text-surface-900-100 leading-relaxed break-words">
      {@html ansiToHtml(line)}
    </div>
  {/each}

  {#if consoleOutput.length === 0}
    <div class="text-surface-600 italic">
      Console ready. Type a command to begin...
    </div>
  {/if}
</div>
