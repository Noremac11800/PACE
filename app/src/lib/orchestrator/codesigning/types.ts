export type IosConfig = { CodesignKey: string; CodesignProvision: string };
export type WindowsConfig = { PackageCertificateThumbprint: string };
export type AndroidConfig = { KeystorePath: string; CodesignInfoTxtPath: string };

export type CodesigningData = {
  ios: Record<string, IosConfig>;
  windows: Record<string, WindowsConfig>;
  android: Record<string, AndroidConfig>;
};
