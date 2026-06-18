export interface NugetSource {
  name: string;
  url: string;
  enabled: boolean;
}

export interface CachedPackage {
  name: string;
  versions: string[];
}
