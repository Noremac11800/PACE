<script module lang="ts">
  import { ContentItem } from "$lib/content-item";
  import { Bug, Ellipsis, Trash2 } from "@lucide/svelte";
  import { Menu, Portal } from "@skeletonlabs/skeleton-svelte";
  export { contentItemGrid, contentItemList, contentItemTable };

  const deleteOption = "delete";
  const debugOption = "debug";

  async function handleEllipsisOptionSelected(
    item: ContentItem,
    details: { value: string },
  ) {
    if (details.value === deleteOption) {
      await item.deleteAsync();
    } else if (details.value === debugOption) {
      console.log(item);
    }
  }
</script>

{#snippet debugInfo(item: ContentItem)}
  <pre>{JSON.stringify(item, null, 2)}</pre>
{/snippet}

{#snippet contentItemGrid(item: ContentItem)}
  <div
    class="relative flex flex-col card card-hover preset-outlined-surface-500 cursor-pointer"
  >
    <img
      class="object-fit max-h-48 rounded-t-lg preset-outlined-surface-500"
      alt="Placeholder"
      src="/book.svg"
    />
    <div class="flex flex-col p-2 bg-surface-200-800/25">
      <h6 class="h6 font-bold">{item.name}</h6>
      <span>
        Created:
        {item.createdDate.toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
      <span>
        Modified:
        {item.modifiedDate.toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
      <span>
        Owner:
        {item.owner.username}
      </span>
    </div>

    <Menu onSelect={(details) => handleEllipsisOptionSelected(item, details)}>
      <Menu.Trigger class="btn preset-filled">
        {#snippet element(attrs)}
          <button
            {...attrs}
            class="btn hover:preset-tonal absolute bottom-2 right-2 aspect-square p-2"
          >
            <Ellipsis />
          </button>
        {/snippet}
      </Menu.Trigger>
      <Portal>
        <Menu.Positioner>
          <Menu.Content>
            <Menu.Item value={deleteOption}>
              <Menu.ItemText>
                {#snippet element(attrs)}
                  <div
                    {...attrs}
                    class="flex flex-row items-center gap-2 text-error-500"
                  >
                    <Trash2 size={16} />
                    Delete
                  </div>
                {/snippet}
              </Menu.ItemText>
            </Menu.Item>
            <Menu.Separator />
            <Menu.Item value={debugOption}>
              <Menu.ItemText>
                {#snippet element(attrs)}
                  <div {...attrs} class="flex flex-row items-center gap-2">
                    <Bug size={16} />
                    Debug
                  </div>
                {/snippet}
              </Menu.ItemText>
            </Menu.Item>
          </Menu.Content>
        </Menu.Positioner>
      </Portal>
    </Menu>
  </div>
{/snippet}

{#snippet contentItemList(item: ContentItem)}
  <div>{item.id}</div>
{/snippet}

{#snippet contentItemTable(item: ContentItem)}
  <div>{item.id}</div>
{/snippet}
