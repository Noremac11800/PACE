import { readable } from "svelte/store";
import { toaster } from "$lib/toaster";
import { toastIconWifi, toastIconWifiOff } from "$lib/snippets/Toasts.svelte";

export const isWifiConnected = readable(navigator.onLine, (set) => {
  let prevConnected = navigator.onLine;

  const update = () => {
    const current = navigator.onLine;
    if (current !== prevConnected) {
      if (current) {
        toaster?.info({
          title: "Wi-Fi connected",
          meta: {
            icon: toastIconWifi,
          },
        });
      } else {
        toaster?.info({
          title: "Wi-Fi disconnected",
          meta: {
            icon: toastIconWifiOff,
          },
        });
      }
    }

    // Using navigator.onLine as a proxy for Wi-Fi connection status
    set(current);
    prevConnected = current;
  };

  update();

  window.addEventListener("online", update);
  window.addEventListener("offline", update);

  return () => {
    window.removeEventListener("online", update);
    window.removeEventListener("offline", update);
  };
});
