import { Command } from "@tauri-apps/plugin-shell";
import { readTextFile } from "@tauri-apps/plugin-fs";
import { homeDir } from "@tauri-apps/api/path";

// Helper to expand $HOME to absolute path
async function expandPath(filePath: string): Promise<string> {
  if (filePath.startsWith("$HOME")) {
    return filePath.replace("$HOME", await homeDir());
  }
  return filePath;
}

export type Platform = "ios" | "android" | "windows";
export type BuildConfig = "Debug" | "Release";

export interface CodesigningData {
  ios: Record<string, { CodesignKey: string; CodesignProvision: string }>;
  windows: Record<string, { PackageCertificateThumbprint: string }>;
  android: Record<
    string,
    {
      KeystorePath: string;
      CodesignInfoTxtPath: string;
    }
  >;
}

export interface AndroidCodesignInfo {
  Alias: string;
  KeyPass: string;
  StorePass: string;
}

export const DEFAULT_CODESIGNING_CONFIG: CodesigningData = {
  ios: { "*": { CodesignKey: "", CodesignProvision: "" } },
  windows: { "*": { PackageCertificateThumbprint: "" } },
  android: { "*": { KeystorePath: "", CodesignInfoTxtPath: "" } },
};

export function getRuntimeForPlatform(platform: Platform): string {
  switch (platform) {
    case "ios":
      return "ios-arm64";
    case "android":
      return "android-arm64";
    case "windows":
      return "win10-x64";
    default:
      return "";
  }
}

export function getFrameworkForPlatform(platform: Platform): string {
  switch (platform) {
    case "ios":
      return "net10.0-ios";
    case "android":
      return "net10.0-android";
    case "windows":
      return "net10.0-windows10.0.20348.0";
    default:
      return "";
  }
}

export async function getCodesigningParams(
  platform: Platform,
  codesigningConfig: CodesigningData,
  androidKey: string | undefined,
  iosBundleId: string | undefined,
  windowsKey: string | undefined,
  androidCodesignInfo: AndroidCodesignInfo | undefined,
): Promise<string[]> {
  const params: string[] = [];
  switch (platform) {
    case "ios":
      if (iosBundleId) {
        const config = codesigningConfig.ios[iosBundleId];
        if (config?.CodesignKey) {
          params.push(`/p:CodesignKey="${config.CodesignKey}"`);
        }
        if (config?.CodesignProvision) {
          params.push(`/p:CodesignProvision="${config.CodesignProvision}"`);
        }
      }
      break;
    case "android":
      if (androidKey) {
        const config = codesigningConfig.android[androidKey];
        if (config?.KeystorePath) {
          params.push("/p:AndroidKeyStore=true");
          const expandedPath = await expandPath(config.KeystorePath);
          params.push(`/p:AndroidSigningKeyStore=${expandedPath}`);
        }
        // Use parsed values from CodesignInfoTxtPath
        if (androidCodesignInfo?.Alias) {
          params.push(`/p:AndroidSigningKeyAlias=${androidCodesignInfo.Alias}`);
        }
        if (androidCodesignInfo?.KeyPass) {
          params.push(
            `/p:AndroidSigningKeyPass=${androidCodesignInfo.KeyPass}`,
          );
        }
        if (androidCodesignInfo?.StorePass) {
          params.push(
            `/p:AndroidSigningStorePass=${androidCodesignInfo.StorePass}`,
          );
        }
      }
      break;
    case "windows":
      if (windowsKey) {
        const config = codesigningConfig.windows[windowsKey];
        if (config?.PackageCertificateThumbprint) {
          params.push("/p:AppxPackageSigningEnabled=true");
          params.push("/p:WindowsPackageType=MSIX");
          params.push(
            `/p:PackageCertificateThumbprint=${config.PackageCertificateThumbprint}`,
          );
        }
      }
      break;
  }
  return params;
}

export async function parseAndroidCodesignInfo(
  filePath: string,
): Promise<AndroidCodesignInfo> {
  try {
    // Expand $HOME if present
    const expandedPath = filePath.replace("$HOME", await homeDir());

    const content = await readTextFile(expandedPath);
    const params: Record<string, string> = {};
    let inCertificateSection = false;

    for (const line of content.split("\n")) {
      const trimmed = line.trim();

      // Check for section header
      if (trimmed === "[certificate]") {
        inCertificateSection = true;
        continue;
      }

      // Skip empty lines and comments
      if (!trimmed || trimmed.startsWith("#")) {
        continue;
      }

      // Stop if we hit another section
      if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
        inCertificateSection = false;
        continue;
      }

      // Parse key=value pairs only in certificate section
      if (inCertificateSection && trimmed.includes("=")) {
        const [key, ...valueParts] = trimmed.split("=");
        params[key.trim().toLowerCase()] = valueParts.join("=").trim();
      }
    }

    // Map INI keys to AndroidCodesignInfo keys
    return {
      Alias: params["alias"] || "",
      KeyPass: params["password"] || "",
      StorePass: params["storepassword"] || "",
    };
  } catch (e) {
    console.error("Failed to parse Android codesign info:", e);
    return { Alias: "", KeyPass: "", StorePass: "" };
  }
}

export interface PublishOptions {
  csprojPath: string;
  buildConfig: BuildConfig;
  runtime: string;
  framework: string;
  noRestore: boolean;
  platform: Platform;
  codesigningParams: string[];
  buildProps?: { name: string; default: string | boolean }[];
  msbuildProps?: Record<string, string>;
}

export function buildPublishCommand(options: PublishOptions): string[] {
  const {
    csprojPath,
    buildConfig,
    runtime,
    framework,
    noRestore,
    platform,
    codesigningParams,
    buildProps = [],
    msbuildProps = {},
  } = options;

  const publishArgs: string[] = [
    "publish",
    ...(platform !== "windows" ? ["--runtime", runtime] : []),
    "--configuration",
    buildConfig,
    "--framework",
    framework,
    "--verbosity",
    "minimal",
  ];

  // iOS builds require the interpreter for publish scenarios
  if (platform === "ios") {
    publishArgs.push("/p:UseInterpreter=true");
  }

  // Add configured build props that differ from their defaults
  for (const prop of buildProps) {
    const val = msbuildProps[prop.name];
    const effective = val !== undefined ? val : String(prop.default);
    if (effective !== "" && effective !== String(prop.default)) {
      publishArgs.push(`/p:${prop.name}=${effective}`);
    }
  }

  // Add platform-specific codesigning params
  publishArgs.push(...codesigningParams);

  publishArgs.push("/p:ArchiveOnBuild=true");
  publishArgs.push("/p:DistributionMethod=enterprise");

  // Add --no-restore if enabled
  if (noRestore) {
    publishArgs.push("--no-restore");
  }

  // Add Android-specific params for Debug builds
  if (platform === "android" && buildConfig === "Debug") {
    publishArgs.push("/p:EmbedAssembliesIntoApk=true");
  }

  // Project path goes last
  publishArgs.push(csprojPath);

  return publishArgs;
}

export async function buildCommandPreview(
  csprojPath: string,
  buildConfig: BuildConfig,
  runtime: string,
  framework: string,
  noRestore: boolean,
  platform: Platform,
  codesigningConfig: CodesigningData,
  androidKey: string | undefined,
  iosBundleId: string | undefined,
  windowsKey: string | undefined,
  androidCodesignInfo: AndroidCodesignInfo | undefined,
  buildProps: { name: string; default: string | boolean }[] = [],
  msbuildProps: Record<string, string> = {},
): Promise<string> {
  const quoteArg = (arg: string): string => {
    if (/[\s'"]/.test(arg)) {
      return `'${arg}'`;
    }
    return arg;
  };

  const runtimeArg = platform !== "windows" ? ` --runtime ${runtime}` : "";
  let preview = `dotnet publish${runtimeArg} --configuration ${buildConfig} --framework ${framework} --verbosity minimal`;

  // iOS builds require the interpreter for publish scenarios
  if (platform === "ios") {
    preview += " /p:UseInterpreter=true";
  }

  // Add configured build props that differ from their defaults
  for (const prop of buildProps) {
    const val = msbuildProps[prop.name];
    const effective = val !== undefined ? val : String(prop.default);
    if (effective !== "" && effective !== String(prop.default)) {
      preview += ` ${quoteArg(`/p:${prop.name}=${effective}`)}`;
    }
  }

  // Add platform-specific codesigning params
  const codesigningParams = await getCodesigningParams(
    platform,
    codesigningConfig,
    androidKey,
    iosBundleId,
    windowsKey,
    androidCodesignInfo,
  );

  for (const param of codesigningParams) {
    preview += ` ${quoteArg(param)}`;
  }

  preview += " /p:ArchiveOnBuild=true";
  preview += " /p:DistributionMethod=enterprise";

  // Add --no-restore if enabled
  if (noRestore) {
    preview += " --no-restore";
  }

  // Add Android-specific params for Debug builds
  if (platform === "android" && buildConfig === "Debug") {
    preview += " /p:EmbedAssembliesIntoApk=true";
  }

  // Project path goes last
  preview += ` ${quoteArg(csprojPath)}`;

  return preview;
}

export async function runPublishCommand(
  options: PublishOptions,
  onOutput: (text: string, type: "out" | "err") => void,
  onComplete: (code: number | null) => void,
): Promise<{
  kill: () => void;
}> {
  const publishArgs = buildPublishCommand(options);

  const cmd = Command.create("dotnet", publishArgs);

  cmd.stdout.on("data", (data: string) => {
    onOutput(data, "out");
  });

  cmd.stderr.on("data", (data: string) => {
    onOutput(data, "err");
  });

  cmd.on("close", (payload: { code: number | null }) => {
    onComplete(payload.code);
  });

  const child = await cmd.spawn();

  return {
    kill: () => child.kill(),
  };
}
