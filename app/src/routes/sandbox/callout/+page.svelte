<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "../+layout.svelte";
  import Callout from "$lib/components/Callout.svelte";

  let areCalloutsCollapsible = $state(false);
  let areCalloutBackgroundsVisible = $state(false);

  const data = getContext<LayoutProps>("data");

  onMount(() => {
    data.title = "Callout";
  });
</script>

<main class="flex flex-col gap-4 p-8">
  <div class="flex items-center gap-2">
    <input
      class="checkbox"
      type="checkbox"
      bind:checked={areCalloutsCollapsible}
    />
    <label for="checkbox">Make callouts collapsible</label>
  </div>

  <div class="flex items-center gap-2">
    <input
      class="checkbox"
      type="checkbox"
      bind:checked={areCalloutBackgroundsVisible}
    />
    <label for="checkbox">Make callout backgrounds visible</label>
  </div>

  <Callout
    type="note"
    message="Note"
    isCollapsible={areCalloutsCollapsible}
    isBackgroundVisible={areCalloutBackgroundsVisible}
  >
    <p>
      Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis
      deserunt voluptatum doloremque, laboriosam officia nam porro corrupti,
      ipsa, recusandae dolores ipsam sequi temporibus neque laudantium nesciunt
      animi. Numquam?
    </p>
  </Callout>
  <Callout
    type="tip"
    message="Tip"
    isCollapsible={areCalloutsCollapsible}
    isBackgroundVisible={areCalloutBackgroundsVisible}
  >
    <p>
      Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis
      deserunt voluptatum doloremque, laboriosam officia nam porro corrupti,
      ipsa, recusandae dolores ipsam sequi temporibus neque laudantium nesciunt
      animi. Numquam?
    </p>
  </Callout>
  <Callout
    type="important"
    message="Important"
    isCollapsible={areCalloutsCollapsible}
    isBackgroundVisible={areCalloutBackgroundsVisible}
  >
    <p>
      Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis
      deserunt voluptatum doloremque, laboriosam officia nam porro corrupti,
      ipsa, recusandae dolores ipsam sequi temporibus neque laudantium nesciunt
      animi. Numquam?
    </p>
  </Callout>
  <Callout
    type="warning"
    message="Warning"
    isCollapsible={areCalloutsCollapsible}
    isBackgroundVisible={areCalloutBackgroundsVisible}
  >
    <p>
      Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis
      deserunt voluptatum doloremque, laboriosam officia nam porro corrupti,
      ipsa, recusandae dolores ipsam sequi temporibus neque laudantium nesciunt
      animi. Numquam?
    </p>
  </Callout>
  <Callout
    type="error"
    message="Error"
    isCollapsible={areCalloutsCollapsible}
    isBackgroundVisible={areCalloutBackgroundsVisible}
  >
    <p>
      Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis
      deserunt voluptatum doloremque, laboriosam officia nam porro corrupti,
      ipsa, recusandae dolores ipsam sequi temporibus neque laudantium nesciunt
      animi. Numquam?
    </p>
  </Callout>
  <Callout
    type="error"
    message="Error"
    isCollapsible={areCalloutsCollapsible}
    isBackgroundVisible={areCalloutBackgroundsVisible}
  >
    <Callout
      type="note"
      message="Note"
      isCollapsible={areCalloutsCollapsible}
      isBackgroundVisible={areCalloutBackgroundsVisible}
    >
      <p>
        quis deserunt voluptatum doloremque, laboriosam officia nam porro
        corrupti, ipsa, recusandae dolores ipsam sequi temporibus neque
        laudantium nesciunt animi. Numquam?
      </p>
    </Callout>
    <div class="h-4"></div>
    <Callout
      type="important"
      message="Important"
      isCollapsible={areCalloutsCollapsible}
      isBackgroundVisible={areCalloutBackgroundsVisible}
    >
      <p>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad
        quis deserunt voluptatum doloremque, laboriosam officia nam porro
        corrupti, ipsa, recusandae dolores ipsam sequi temporibus neque
        laudantium nesciunt animi. Numquam?
      </p>
    </Callout>
    <div class="h-4"></div>
    <Callout
      type="tip"
      message="Tip"
      isCollapsible={areCalloutsCollapsible}
      isBackgroundVisible={areCalloutBackgroundsVisible}
    >
      <p>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad
        quis deserunt voluptatum doloremque, laboriosam officia nam porro
        corrupti, ipsa, recusandae dolores ipsam sequi temporibus neque
        laudantium nesciunt animi. Numquam?
      </p>
    </Callout>
  </Callout>
</main>
