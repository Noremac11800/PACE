import {
  BaseDirectory,
  readTextFile,
  writeTextFile,
  readDir,
  mkdir,
  remove,
} from "@tauri-apps/plugin-fs";
import { homeDir } from "@tauri-apps/api/path";
import * as TOML from "js-toml";
import type { PaceConfig, PaceProject } from "$lib/types/pace-config";
import { settings } from "$lib/state/settings.svelte";
import { saveSettings } from "$lib/utils/app-init";

export interface ConfigEntry {
  filename: string;
  displayName: string;
}

export const configStore: {
  availableConfigs: ConfigEntry[];
  activeConfigName: string | null;
  activeConfig: PaceConfig | null;
  loading: boolean;
  error: string | null;
} = $state({
  availableConfigs: [],
  activeConfigName: null,
  activeConfig: null,
  loading: false,
  error: null,
});

export function emptyProject(): PaceProject {
  return {
    name: "",
    csproj_path: "",
    repo_url: "",
    sln_group: "",
    explicit_frameworks: [],
    depends_on: [],
  };
}

export function emptyConfig(): PaceConfig {
  return {
    repodir: "",
    projects: [],
    build_props: [],
  };
}

export async function loadAvailableConfigs(): Promise<void> {
  try {
    await mkdir(".pace/configs", {
      baseDir: BaseDirectory.Home,
      recursive: true,
    });

    const entries = await readDir(".pace/configs", {
      baseDir: BaseDirectory.Home,
    });

    configStore.availableConfigs = entries
      .filter((e) => e.name?.endsWith(".toml"))
      .map((e) => ({
        filename: e.name!,
        displayName: e.name!.replace(/\.toml$/, ""),
      }));
  } catch (error) {
    console.error("Failed to list configs:", error);
    configStore.availableConfigs = [];
  }
}

export async function loadConfig(filename: string): Promise<void> {
  configStore.loading = true;
  configStore.error = null;
  try {
    const content = await readTextFile(`.pace/configs/${filename}`, {
      baseDir: BaseDirectory.Home,
    });
    const parsed = TOML.load(content) as Record<string, unknown>;
    configStore.activeConfig = {
      repodir: (parsed.repodir as string) ?? "",
      projects: (parsed.projects as PaceConfig["projects"]) ?? [],
      build_props:
        ((parsed["build-props"] ??
          parsed.build_props) as PaceConfig["build_props"]) ?? [],
      nuget_cache_path:
        (parsed.nuget_cache_path as string | undefined) ?? undefined,
    };
    configStore.activeConfigName = filename;
    settings.lastActiveConfig = filename;
    saveSettings().catch((e) =>
      console.error("Failed to persist lastActiveConfig:", e),
    );
  } catch (error) {
    configStore.error = `Failed to load ${filename}: ${error}`;
    configStore.activeConfig = null;
  } finally {
    configStore.loading = false;
  }
}

export async function saveConfig(
  filename: string,
  config: PaceConfig,
): Promise<void> {
  const content = serializeToml(config);
  await writeTextFile(`.pace/configs/${filename}`, content, {
    baseDir: BaseDirectory.Home,
  });
  await loadAvailableConfigs();
}

export async function createNewConfig(filename: string): Promise<void> {
  const name = filename.endsWith(".toml") ? filename : `${filename}.toml`;
  const content = serializeToml(emptyConfig());
  await writeTextFile(`.pace/configs/${name}`, content, {
    baseDir: BaseDirectory.Home,
  });
  await loadAvailableConfigs();
  await loadConfig(name);
}

export async function duplicateConfig(
  sourceFilename: string,
  newFilename: string,
): Promise<void> {
  const sourceName = sourceFilename.endsWith(".toml")
    ? sourceFilename
    : `${sourceFilename}.toml`;
  const newName = newFilename.endsWith(".toml")
    ? newFilename
    : `${newFilename}.toml`;

  const content = await readTextFile(`.pace/configs/${sourceName}`, {
    baseDir: BaseDirectory.Home,
  });
  await writeTextFile(`.pace/configs/${newName}`, content, {
    baseDir: BaseDirectory.Home,
  });
  await loadAvailableConfigs();
  await loadConfig(newName);
}

export async function renameConfig(
  oldFilename: string,
  newFilename: string,
): Promise<void> {
  const oldName = oldFilename.endsWith(".toml")
    ? oldFilename
    : `${oldFilename}.toml`;
  const newName = newFilename.endsWith(".toml")
    ? newFilename
    : `${newFilename}.toml`;

  const content = await readTextFile(`.pace/configs/${oldName}`, {
    baseDir: BaseDirectory.Home,
  });
  await writeTextFile(`.pace/configs/${newName}`, content, {
    baseDir: BaseDirectory.Home,
  });
  await remove(`.pace/configs/${oldName}`, { baseDir: BaseDirectory.Home });
  await loadAvailableConfigs();

  // If we renamed the active config, update the active config name and reload
  if (configStore.activeConfigName === oldName) {
    configStore.activeConfigName = newName;
    await loadConfig(newName);
  }
}

export async function deleteConfig(filename: string): Promise<void> {
  const name = filename.endsWith(".toml") ? filename : `${filename}.toml`;
  await remove(`.pace/configs/${name}`, { baseDir: BaseDirectory.Home });
  await loadAvailableConfigs();

  // If we deleted the active config, clear it
  if (configStore.activeConfigName === name) {
    configStore.activeConfig = null;
    configStore.activeConfigName = null;
  }
}

export async function importConfig(
  filePath: string,
  filename: string,
): Promise<{ success: boolean; error?: string }> {
  const name = filename.endsWith(".toml") ? filename : `${filename}.toml`;

  try {
    // Read the file content
    const content = await readTextFile(filePath);

    // Validate TOML parsing
    const parsed = TOML.load(content) as Record<string, unknown>;

    // Basic validation: check it has expected structure
    if (!parsed.repodir && !parsed.projects) {
      return {
        success: false,
        error: "Invalid config file: missing repodir or projects",
      };
    }

    // Write to configs directory
    await writeTextFile(`.pace/configs/${name}`, content, {
      baseDir: BaseDirectory.Home,
    });

    await loadAvailableConfigs();
    await loadConfig(name);

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export async function getActiveConfigPath(): Promise<string | null> {
  if (!configStore.activeConfigName) return null;
  const home = await homeDir();
  return `${home}/.pace/configs/${configStore.activeConfigName}`;
}

export async function paceArgs(args: string[]): Promise<string[]> {
  const configPath = await getActiveConfigPath();
  if (configPath) {
    return ["-C", configPath, ...args];
  }
  return args;
}

function serializeToml(config: PaceConfig): string {
  const lines: string[] = [];

  if (config.repodir) {
    lines.push(`repodir = ${JSON.stringify(config.repodir)}`);
    lines.push("");
  }

  if (config.nuget_cache_path) {
    lines.push(`nuget_cache_path = ${JSON.stringify(config.nuget_cache_path)}`);
    lines.push("");
  }

  for (const project of config.projects) {
    lines.push("[[projects]]");
    lines.push(`name = ${JSON.stringify(project.name)}`);
    lines.push(`csproj_path = ${JSON.stringify(project.csproj_path)}`);
    if (project.repo_url !== undefined && project.repo_url !== "") {
      lines.push(`repo_url = ${JSON.stringify(project.repo_url)}`);
    }
    if (project.sln_group) {
      lines.push(`sln_group = ${JSON.stringify(project.sln_group)}`);
    }
    const frameworks = project.explicit_frameworks ?? [];
    lines.push(
      `explicit_frameworks = [${frameworks.map((f) => JSON.stringify(f)).join(", ")}]`,
    );
    const deps = project.depends_on ?? [];
    lines.push(
      `depends_on = [${deps.map((d) => JSON.stringify(d)).join(", ")}]`,
    );
    lines.push("");
  }

  for (const section of config.build_props ?? []) {
    lines.push(`[["build-props"]]`);
    for (const [key, value] of Object.entries(section)) {
      if (Array.isArray(value)) {
        lines.push(
          `${key} = [${value.map((v) => JSON.stringify(v)).join(", ")}]`,
        );
      } else if (value !== undefined && value !== null) {
        lines.push(`${key} = ${JSON.stringify(value)}`);
      }
    }
    lines.push("");
  }

  return lines.join("\n");
}
