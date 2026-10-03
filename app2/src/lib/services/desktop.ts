import { Channel, invoke, isTauri } from "@tauri-apps/api/core";
import { open, save } from "@tauri-apps/plugin-dialog";
import { revealItemInDir } from "@tauri-apps/plugin-opener";
import type { Environment, RuntimeOptions } from "$lib/domain/types";

export const desktop = isTauri();

export const environment = () => invoke<Environment>("environment");

export async function request<T>(
    options: RuntimeOptions,
    payload: Record<string, unknown>,
) {
    return invoke<{ data: T; warnings: string }>("bridge", {
        options,
        request: payload,
    });
}

export async function execute(
    options: RuntimeOptions,
    args: string[],
    onOutput: (text: string) => void,
) {
    const output = new Channel<{ stream: string; text: string }>();
    output.onmessage = (line) => onOutput(line.text + "\n");
    return invoke<number>("run_pace", { options, args, output });
}

export const chooseConfig = () =>
    open({
        title: "Open PACE configuration",
        multiple: false,
        filters: [{ name: "TOML configuration", extensions: ["toml"] }],
    });
export const chooseSavePath = () =>
    save({
        title: "Save configuration as",
        defaultPath: "workspace.toml",
        filters: [{ name: "TOML configuration", extensions: ["toml"] }],
    });
export const chooseDirectory = () =>
    open({ title: "Working directory", directory: true, multiple: false });
export const choosePython = () =>
    open({ title: "Python executable containing pacev2", multiple: false });
export const reveal = (path: string) => revealItemInDir(path);
