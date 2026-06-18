<script lang="ts">
  let {
    value = $bindable(""),
    placeholder,
    confirmLabel,
    busy = false,
    oncancel,
    onconfirm,
  }: {
    value?: string;
    placeholder: string;
    confirmLabel: string;
    busy?: boolean;
    oncancel: () => void;
    onconfirm: () => void;
  } = $props();

  function focusOnMount(node: HTMLElement): void {
    node.focus();
  }
</script>

<div class="px-3 py-2 flex gap-2">
  <input
    class="flex-1 px-2 py-1.5 rounded border border-surface-300-700 bg-surface-100-900 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
    type="text"
    {placeholder}
    bind:value
    onkeydown={(e) => e.key === "Enter" && onconfirm()}
    use:focusOnMount
  />
  <button class="btn preset-tonal text-xs px-2 py-1" onclick={oncancel}>
    Cancel
  </button>
  <button
    class="btn preset-filled-primary-500 text-xs px-2 py-1"
    onclick={onconfirm}
    disabled={busy || !value.trim()}
  >
    {busy ? "…" : confirmLabel}
  </button>
</div>
