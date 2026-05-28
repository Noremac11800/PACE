<script lang="ts">
  import { onMount, tick } from "svelte";
  import { Command, open } from "@tauri-apps/plugin-shell";
  import {
    Terminal,
    Play,
    Square,
    Trash2,
    Copy,
    Download,
    FolderOpen,
    RotateCcw,
    ChevronDown,
    Settings2,
  } from "@lucide/svelte";

  // Console state
  let consoleOutput = $state<string[]>([]);
  let commandInput = $state("");
  let commandHistory = $state<string[]>([]);
  let historyIndex = $state(-1);
  let isRunning = $state(false);
  let currentProcess: any = null;
  let consoleRef: HTMLDivElement;
  let inputRef: HTMLInputElement;
  let autoScroll = $state(true);
  let showTimestamps = $state(true);
  let workingDirectory = $state("$HOME");

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

  function getTimestamp(): string {
    if (!showTimestamps) return "";
    const now = new Date();
    return `[${now.toLocaleTimeString()}] `;
  }

  function addOutput(
    text: string,
    type: "input" | "output" | "error" = "output",
  ) {
    const prefix = type === "input" ? "$ " : type === "error" ? "! " : "  ";
    const timestamp = getTimestamp();
    const line = `${timestamp}${prefix}${text}`;
    consoleOutput = [...consoleOutput, line];

    if (autoScroll) {
      tick().then(() => {
        if (consoleRef) {
          consoleRef.scrollTop = consoleRef.scrollHeight;
        }
      });
    }
  }

  async function executeCommand(cmd: string) {
    if (!cmd.trim() || isRunning) return;

    // Add to history
    if (!commandHistory.includes(cmd)) {
      commandHistory = [cmd, ...commandHistory].slice(0, 50);
    }
    historyIndex = -1;

    // Show command
    addOutput(cmd, "input");
    commandInput = "";
    isRunning = true;

    try {
      // Parse command
      const parts = cmd.trim().split(/\s+/);
      const command = parts[0];
      const args = parts.slice(1);

      // Handle special commands
      if (command === "clear" || command === "cls") {
        consoleOutput = [];
        isRunning = false;
        return;
      }

      if (command === "cd") {
        if (args.length === 0) {
          workingDirectory = "$HOME";
        } else {
          workingDirectory = args.join(" ");
        }
        addOutput(`Changed directory to: ${workingDirectory}`);
        isRunning = false;
        return;
      }

      if (command === "pwd") {
        addOutput(workingDirectory);
        isRunning = false;
        return;
      }

      if (command === "echo") {
        addOutput(args.join(" "));
        isRunning = false;
        return;
      }

      if (command === "help") {
        addOutput("Available commands:");
        addOutput("  clear/cls   - Clear console");
        addOutput("  cd <dir>    - Change working directory");
        addOutput("  pwd         - Show current directory");
        addOutput("  echo <text> - Print text");
        addOutput("  help        - Show this help");
        addOutput("  pace <cmd>  - Run PACE CLI commands");
        addOutput("  git <cmd>   - Run git commands");
        addOutput("");
        addOutput("Features:");
        addOutput("  ↑/↓         - Navigate command history");
        addOutput("  Tab         - Auto-complete (coming soon)");
        addOutput("  Ctrl+C      - Cancel running command");
        isRunning = false;
        return;
      }

      // Create and spawn command to get a killable Child process
      const tauriCmd = Command.create(command, args);
      const child = await tauriCmd.spawn();
      currentProcess = child;

      // Set up event listeners for real-time output
      tauriCmd.stdout.on("data", (data: string) => {
        addOutput(data);
      });

      tauriCmd.stderr.on("data", (data: string) => {
        addOutput(data, "error");
      });

      // Wait for process to exit
      const exitCode = await new Promise<number>((resolve) => {
        tauriCmd.on(
          "close",
          (data: { code: number | null; signal?: number | null }) => {
            resolve(data.code ?? 0);
          },
        );
      });

      addOutput(`Exit code: ${exitCode}`);
    } catch (error) {
      addOutput(
        `Error: ${error instanceof Error ? error.message : String(error)}`,
        "error",
      );
    } finally {
      isRunning = false;
      currentProcess = null;
    }
  }

  function cancelCommand() {
    if (currentProcess) {
      currentProcess.kill();
      addOutput("Command cancelled", "error");
      isRunning = false;
      currentProcess = null;
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      executeCommand(commandInput);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (historyIndex < commandHistory.length - 1) {
        historyIndex++;
        commandInput = commandHistory[historyIndex];
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex > 0) {
        historyIndex--;
        commandInput = commandHistory[historyIndex];
      } else {
        historyIndex = -1;
        commandInput = "";
      }
    } else if (e.key === "c" && e.ctrlKey) {
      e.preventDefault();
      cancelCommand();
    } else if (e.key === "l" && e.ctrlKey) {
      e.preventDefault();
      consoleOutput = [];
    }
  }

  function clearConsole() {
    consoleOutput = [];
    inputRef?.focus();
  }

  function copyToClipboard() {
    const text = consoleOutput.join("\n");
    navigator.clipboard.writeText(text);
    addOutput("Console content copied to clipboard");
  }

  function downloadOutput() {
    const text = consoleOutput.join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pace-console-${new Date().toISOString().slice(0, 19)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    addOutput("Console output downloaded");
  }

  async function openWorkingDir() {
    try {
      await open(workingDirectory === "$HOME" ? "~" : workingDirectory);
    } catch (error) {
      addOutput(`Failed to open directory: ${error}`, "error");
    }
  }

  function runPresetCommand(cmd: string) {
    commandInput = cmd;
    executeCommand(cmd);
  }

  onMount(() => {
    // Welcome message
    addOutput("╔════════════════════════════════════════╗");
    addOutput("║     PACE Console - Ready              ║");
    addOutput("╚════════════════════════════════════════╝");
    addOutput("");
    addOutput("Type 'help' for available commands");
    addOutput("Use ↑/↓ to navigate command history");
    addOutput("Press Ctrl+C to cancel running commands");
    addOutput("");

    inputRef?.focus();
  });
</script>

<div class="h-full flex flex-col bg-surface-100-900">
  <!-- Toolbar -->
  <div
    class="flex items-center gap-2 p-2 bg-surface-200-800 border-b border-surface-300-700"
  >
    <span class="text-xs font-mono text-surface-700-300 px-2">PACE Console</span
    >
    <div class="flex-1"></div>

    <!-- Quick Commands -->
    <div class="flex items-center gap-1">
      <button
        class="btn preset-tonal px-2 py-1 text-xs"
        onclick={() => runPresetCommand("pace git pull")}
        disabled={isRunning}
        title="pace git pull"
      >
        <RotateCcw size={14} class="mr-1" />
        git pull
      </button>
      <button
        class="btn preset-tonal px-2 py-1 text-xs"
        onclick={() => runPresetCommand("pace git clone")}
        disabled={isRunning}
        title="pace git clone"
      >
        <Download size={14} class="mr-1" />
        git clone
      </button>
      <button
        class="btn preset-tonal px-2 py-1 text-xs"
        onclick={() => runPresetCommand("pace --help")}
        disabled={isRunning}
        title="pace --help"
      >
        <Terminal size={14} class="mr-1" />
        help
      </button>
    </div>

    <div class="w-px h-6 bg-surface-400-600 mx-2"></div>

    <!-- Console Controls -->
    <div class="flex items-center gap-1">
      <button
        class="btn preset-tonal p-1.5"
        onclick={clearConsole}
        title="Clear console (Ctrl+L)"
      >
        <Trash2 size={14} />
      </button>
      <button
        class="btn preset-tonal p-1.5"
        onclick={copyToClipboard}
        title="Copy to clipboard"
      >
        <Copy size={14} />
      </button>
      <button
        class="btn preset-tonal p-1.5"
        onclick={downloadOutput}
        title="Download output"
      >
        <Download size={14} />
      </button>
      <button
        class="btn preset-tonal p-1.5"
        onclick={openWorkingDir}
        title="Open working directory"
      >
        <FolderOpen size={14} />
      </button>
    </div>

    <div class="w-px h-6 bg-surface-400-600 mx-2"></div>

    <!-- Settings -->
    <div class="flex items-center gap-1">
      <button
        class="btn {autoScroll
          ? 'preset-filled-primary-500'
          : 'preset-tonal'} p-1.5"
        onclick={() => (autoScroll = !autoScroll)}
        title="Auto-scroll"
      >
        <ChevronDown size={14} />
      </button>
      <button
        class="btn {showTimestamps
          ? 'preset-filled-primary-500'
          : 'preset-tonal'} p-1.5"
        onclick={() => (showTimestamps = !showTimestamps)}
        title="Show timestamps"
      >
        <Settings2 size={14} />
      </button>
    </div>
  </div>

  <!-- Console Output -->
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

  <!-- Command Input -->
  <div class="p-3 bg-surface-200-800 border-t border-surface-300-700">
    <div class="flex items-center gap-2">
      <span class="text-primary-500 font-mono text-sm font-bold">$</span>
      <input
        bind:this={inputRef}
        bind:value={commandInput}
        onkeydown={handleKeyDown}
        placeholder={isRunning
          ? "Running... (Ctrl+C to cancel)"
          : "Type a command..."}
        disabled={isRunning}
        class="flex-1 bg-transparent border-none outline-none font-mono text-sm text-surface-900-100 placeholder:text-surface-500-600"
        spellcheck="false"
        autocomplete="off"
      />

      {#if isRunning}
        <button
          class="btn preset-filled-error-500 p-2"
          onclick={cancelCommand}
          title="Cancel command"
        >
          <Square size={16} />
        </button>
      {:else}
        <button
          class="btn preset-filled-primary-500 p-2"
          onclick={() => executeCommand(commandInput)}
          disabled={!commandInput.trim()}
          title="Run command"
        >
          <Play size={16} />
        </button>
      {/if}
    </div>

    <!-- Status Bar -->
    <div
      class="flex items-center justify-between mt-2 text-xs text-surface-500"
    >
      <span class="font-mono">{workingDirectory}</span>
      <span>
        {isRunning ? "Running..." : "Ready"}
        {#if commandHistory.length > 0}
          • {commandHistory.length} in history
        {/if}
      </span>
    </div>
  </div>
</div>
