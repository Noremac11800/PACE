<script lang="ts">
  import { GitBranch } from "@lucide/svelte";
  import { revealItemInDir } from "@tauri-apps/plugin-opener";
  import { untrack } from "svelte";
  import { configStore } from "$lib/config-store.svelte";
  import {
    loadGitStatuses,
    getGitStatus,
    isLoadingGit,
    clearGitStatuses,
  } from "$lib/git-status.svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import { paceArgs } from "$lib/config-store.svelte";
  import type { PaceProject } from "$lib/pace-config";
  import GitActions from "$lib/orchestrator/git-tab/GitActions.svelte";
  import GitGroupCard from "$lib/orchestrator/git-tab/GitGroupCard.svelte";

  let refreshing = $state(false);
  let cloning = $state(false);
  let pulling = $state(false);
  let expandedGroups = $state<Set<string>>(new Set());
  let hasLoaded = $state(false);
  let lastOperationResult = $state<{
    type: "clone" | "pull" | null;
    success: boolean;
    message: string;
  }>({ type: null, success: true, message: "" });

  $effect(() => {
    if (configStore.activeConfig) {
      // Prevent infinite loops by using untrack
      const config = untrack(() => configStore.activeConfig);
      const loaded = untrack(() => hasLoaded);

      if (!loaded && config) {
        hasLoaded = true;
        loadGitStatuses(config);
        // Expand all groups by default in Git tab
        const allGroups = getOrderedGroups();
        expandedGroups = new Set(allGroups);
      }
    }
  });

  function getOrderedGroups(): string[] {
    if (!configStore.activeConfig) return [];
    const groups = configStore.activeConfig.projects
      .map((p) => p.sln_group)
      .filter(Boolean) as string[];
    return [...new Set(groups)];
  }

  function getProjectsByGroup(group: string): PaceProject[] {
    if (!configStore.activeConfig) return [];
    return configStore.activeConfig.projects.filter(
      (p) => p.sln_group === group && p.repo_url,
    );
  }

  function toggleGroup(group: string) {
    const newSet = new Set(expandedGroups);
    if (newSet.has(group)) {
      newSet.delete(group);
    } else {
      newSet.add(group);
    }
    expandedGroups = newSet;
  }

  function isGroupExpanded(group: string): boolean {
    return expandedGroups.has(group);
  }

  async function refreshAll() {
    if (!configStore.activeConfig || refreshing) return;
    clearGitStatuses();
    refreshing = true;
    await loadGitStatuses(configStore.activeConfig);
    refreshing = false;
  }

  async function runGitClone() {
    if (!configStore.activeConfig || cloning || pulling) return;
    clearGitStatuses();
    cloning = true;
    lastOperationResult = { type: null, success: true, message: "" };
    try {
      const allArgs = await paceArgs(["git", "clone"]);
      const cmd = Command.create("pace", allArgs);
      const result = await cmd.execute();
      if (result.code === 0) {
        lastOperationResult = {
          type: "clone",
          success: true,
          message: "All repositories cloned successfully",
        };
      } else {
        const errorOutput =
          result.stderr || "One or more repositories failed to clone";
        lastOperationResult = {
          type: "clone",
          success: false,
          message: errorOutput,
        };
      }
    } catch (e) {
      console.error("Git clone failed:", e);
      lastOperationResult = {
        type: "clone",
        success: false,
        message: String(e),
      };
    } finally {
      cloning = false;
      await loadGitStatuses(configStore.activeConfig);
    }
  }

  async function runGitPull() {
    if (!configStore.activeConfig || cloning || pulling) return;
    clearGitStatuses();
    pulling = true;
    lastOperationResult = { type: null, success: true, message: "" };
    try {
      const allArgs = await paceArgs(["git", "pull"]);
      const cmd = Command.create("pace", allArgs);
      const result = await cmd.execute();
      if (result.code === 0) {
        lastOperationResult = {
          type: "pull",
          success: true,
          message: "All repositories pulled successfully",
        };
      } else {
        const errorOutput =
          result.stderr || "One or more repositories failed to pull";
        lastOperationResult = {
          type: "pull",
          success: false,
          message: errorOutput,
        };
      }
    } catch (e) {
      console.error("Git pull failed:", e);
      lastOperationResult = {
        type: "pull",
        success: false,
        message: String(e),
      };
    } finally {
      pulling = false;
      await loadGitStatuses(configStore.activeConfig);
    }
  }

  async function openRepoFolder(project: PaceProject) {
    if (!configStore.activeConfig) return;
    const path = `${configStore.activeConfig.repodir}/${project.name}`;
    await revealItemInDir(path);
  }

  function getAllProjectsWithRepo(): PaceProject[] {
    if (!configStore.activeConfig) return [];
    return configStore.activeConfig.projects.filter((p) => p.repo_url);
  }

  function getProjectStatusSummary() {
    const projects = getAllProjectsWithRepo();
    const cloned = projects.filter((p) => getGitStatus(p)?.cloned).length;
    const upToDate = projects.filter((p) => {
      const status = getGitStatus(p);
      return status?.cloned && status?.upToDate;
    }).length;
    const loading = projects.filter((p) => isLoadingGit(p)).length;
    return { total: projects.length, cloned, upToDate, loading };
  }
</script>

<div class="h-full flex flex-col overflow-hidden">
  <!-- Header with actions -->
  <div
    class="flex items-center justify-between gap-4 p-4 border-b border-surface-200-800 bg-surface-50-950 shrink-0"
  >
    <div class="flex items-center gap-3">
      <GitBranch size={20} class="text-primary-500" />
      <h3 class="font-semibold text-surface-900-100">Git Status</h3>
      {#if configStore.activeConfig}
        {@const summary = getProjectStatusSummary()}
        <div class="flex items-center gap-2 text-xs">
          <span
            class="px-2 py-0.5 rounded bg-surface-200-800 text-surface-700-300"
          >
            {summary.total} repos
          </span>
          {#if cloning}
            <span
              class="px-2 py-0.5 rounded bg-primary-500/10 text-primary-500"
            >
              Cloning...
            </span>
          {:else if pulling}
            <span
              class="px-2 py-0.5 rounded bg-primary-500/10 text-primary-500"
            >
              Pulling...
            </span>
          {:else if summary.loading > 0}
            <span
              class="px-2 py-0.5 rounded bg-primary-500/10 text-primary-500"
            >
              {summary.loading} checking...
            </span>
          {:else}
            <span
              class="px-2 py-0.5 rounded bg-success-500/10 text-success-500"
            >
              {summary.cloned} cloned
            </span>
            <span
              class="px-2 py-0.5 rounded {summary.upToDate === summary.cloned
                ? 'bg-success-500/10 text-success-500'
                : 'bg-warning-500/10 text-warning-500'}"
            >
              {summary.upToDate} up to date
            </span>
          {/if}
        </div>
      {/if}
    </div>
    <GitActions
      {cloning}
      {pulling}
      {refreshing}
      disabled={!configStore.activeConfig}
      onclone={runGitClone}
      onpull={runGitPull}
      onrefresh={refreshAll}
    />
  </div>

  <!-- Status Message Banner -->
  {#if lastOperationResult.type && !cloning && !pulling}
    <div
      class="px-4 py-2 border-b {lastOperationResult.success
        ? 'bg-success-500/10 border-success-500/20'
        : 'bg-error-500/10 border-error-500/20'}"
    >
      <div class="flex items-center gap-2">
        {#if lastOperationResult.success}
          <span class="text-success-500 text-sm font-medium">
            {lastOperationResult.message}
          </span>
        {:else}
          <span class="text-error-500 text-sm font-medium">
            {lastOperationResult.type === "clone" ? "Clone" : "Pull"} failed:
            {lastOperationResult.message}
          </span>
        {/if}
        <button
          class="ml-auto text-xs text-surface-500-400 hover:text-surface-900-100"
          onclick={() =>
            (lastOperationResult = { type: null, success: true, message: "" })}
        >
          Dismiss
        </button>
      </div>
    </div>
  {/if}

  <!-- Content -->
  <div class="flex-1 overflow-auto p-4">
    {#if !configStore.activeConfig}
      <div class="flex items-center justify-center h-full text-surface-500-400">
        No config loaded
      </div>
    {:else if getAllProjectsWithRepo().length === 0}
      <div class="flex items-center justify-center h-full text-surface-500-400">
        No projects with repositories configured
      </div>
    {:else}
      <div class="flex flex-col gap-3">
        {#each getOrderedGroups() as group (group)}
          {@const groupProjects = getProjectsByGroup(group)}
          {#if groupProjects.length > 0}
            <GitGroupCard
              {group}
              projects={groupProjects}
              expanded={isGroupExpanded(group)}
              ontoggle={() => toggleGroup(group)}
              onopenFolder={openRepoFolder}
            />
          {/if}
        {/each}
      </div>
    {/if}
  </div>
</div>
