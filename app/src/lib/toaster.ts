import { createToaster } from "@skeletonlabs/skeleton-svelte";

let toaster: ReturnType<typeof createToaster> | undefined;

export function setToaster(t: ReturnType<typeof createToaster>) {
  toaster = t;
}

export { toaster };
