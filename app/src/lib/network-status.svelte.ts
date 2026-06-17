import { toaster } from "$lib/toaster";
import { toastIconWifi, toastIconWifiOff } from "$lib/snippets/Toasts.svelte";

let online = $state(navigator.onLine);

export const networkStatus = {
  get online() {
    return online;
  },
};

$effect.root(() => {
  let prevConnected = navigator.onLine;

  const update = () => {
    const current = navigator.onLine;
    if (current !== prevConnected) {
      if (current) {
        toaster?.info({
          title: "Wi-Fi connected",
          meta: { icon: toastIconWifi },
        });
      } else {
        toaster?.info({
          title: "Wi-Fi disconnected",
          meta: { icon: toastIconWifiOff },
        });
      }
    }
    online = current;
    prevConnected = current;
  };

  window.addEventListener("online", update);
  window.addEventListener("offline", update);

  return () => {
    window.removeEventListener("online", update);
    window.removeEventListener("offline", update);
  };
});
