<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "../+layout.svelte";
  import { KeyRound, User, Search, Eye, EyeOff, CircleX } from "@lucide/svelte";

  const data = getContext<LayoutProps>("data");

  onMount(() => {
    data.title = "Inputbox";
  });

  let isPasswordVisible = $state(false);
  let username = $state("");
  let search = $state("");
</script>

<main class="flex flex-col gap-4 p-8">
  <div class="input-group grid grid-cols-[auto_1fr_auto]">
    <div class="ig-cell preset-tonal">
      <User />
    </div>
    <input
      class="ig-input"
      type="text"
      placeholder="Username"
      bind:value={username}
    />
    <button
      class="ig-cell btn border-none"
      type="button"
      onclick={() => (username = "")}
    >
      <CircleX size={16} />
    </button>
  </div>

  <div class="input-group grid grid-cols-[auto_1fr_auto]">
    <div class="ig-cell preset-tonal">
      <KeyRound />
    </div>
    <input
      class="ig-input"
      type={isPasswordVisible ? "text" : "password"}
      placeholder="Password"
    />
    <button
      class="ig-cell btn border-none"
      type="button"
      onclick={() => (isPasswordVisible = !isPasswordVisible)}
    >
      {#if isPasswordVisible}
        <Eye size={16} />
      {:else}
        <EyeOff size={16} />
      {/if}
    </button>
  </div>

  <div class="input-group grid grid-cols-[auto_1fr_auto]">
    <div class="ig-cell preset-tonal">
      <Search />
    </div>
    <input
      class="ig-input"
      type="text"
      placeholder="Search"
      bind:value={search}
    />
    <button
      class="ig-cell btn border-none"
      type="button"
      onclick={() => (search = "")}
    >
      <CircleX size={16} />
    </button>
  </div>
</main>
