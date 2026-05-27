<script lang="ts">
  import {
    House,
    Package,
    Terminal,
    CircleQuestionMark,
    FileCode,
  } from "@lucide/svelte";
  import { View } from "./view-types";

  interface Props {
    activeView: View;
  }

  let { activeView = $bindable() }: Props = $props();
</script>

<aside
  class="flex flex-col items-center gap-2 p-2 bg-surface-50-950 border-r border-surface-200-800"
>
  <button
    class="btn {activeView === View.HOME
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.HOME)}
    title="Home"
  >
    <House size={20} />
  </button>
  <button
    class="btn {activeView === View.DEPENDENCIES
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.DEPENDENCIES)}
    title="Dependencies"
  >
    <Package size={20} />
  </button>
  <button
    class="btn {activeView === View.DIRECTORY_BUILD_PROPS
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.DIRECTORY_BUILD_PROPS)}
    title="Directory.Build.props"
  >
    <FileCode size={20} />
  </button>
  <button
    class="btn {activeView === View.CONSOLE
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.CONSOLE)}
    title="Console"
  >
    <Terminal size={20} />
  </button>
  <button
    class="btn {activeView === View.ABOUT
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.ABOUT)}
    title="About"
  >
    <CircleQuestionMark size={20} />
  </button>
</aside>
