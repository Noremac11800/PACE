<script module lang="ts">
  import { Wifi, WifiOff } from "@lucide/svelte";
  export { toastIconWifi, toastIconWifiOff };
</script>

{#snippet toastIconWifi()}
  <Wifi />
{/snippet}

{#snippet toastIconWifiOff()}
  <WifiOff />
{/snippet}
