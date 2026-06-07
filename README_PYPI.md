# **P**roject **A**utomation and **C**onfiguration **E**ngine

> A Python CLI tool for bulk management of C# .NET project ecosystems — from single class libraries to complex multi-project hierarchies with MAUI applications.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![.NET](https://img.shields.io/badge/.NET-10.0+-purple?logo=dotnet&logoColor=white)](https://dotnet.microsoft.com)
[![MAUI](https://img.shields.io/badge/MAUI-supported-blueviolet?logo=dotnet)](https://dotnet.microsoft.com/apps/maui)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

## Overview

PACE eliminates the repetitive, error-prone manual work of managing .NET project ecosystems at scale. Rather than shelling into each project directory to run `dotnet` commands, manage git state, or manually update build configurations, PACE provides a unified interface to interact with all of them at once.

It understands your project topology — respecting dependency order, project hierarchy, and configuration context — so you can express intent once and apply it across your entire repository graph.

## Target project types

| Type | Description |
|------|-------------|
| **Class libraries** | Standalone or NuGet-published reusable packages |
| **MAUI applications** | Cross-platform apps with platform image and build assets |
| **Dependency trees** | Multi-library hierarchies with topological dependency ordering |
| **Sample applications** | Reference and demo apps accompanying library suites |

## Design principles

**Composability** — individual commands can be piped, scripted, and combined into workflows.

**Topology-awareness** — multi-project operations always respect inter-project dependencies.

**Transparency** — every operation emits clear, structured output suitable for both human review and CI log parsing.

**Reproducibility** — configuration is declared in a manifest file that describes the project graph.

## Installation

```bash
pip install pace-dotnet
```

## Configuration

PACE is driven by a `pace.toml` manifest at your workspace root:

```toml
repodir = "/path/to/repositories"
nuget_cache_path = "/path/to/nuget/cache"

[[projects]]
name = "common-lib"
csproj_path = "common-lib/src/CommonLib/CommonLib.csproj"
repo_url = "https://github.com/org/common-lib"
depends_on = []

[[projects]]
name = "feature-module"
csproj_path = "feature-module/src/FeatureModule/FeatureModule.csproj"
repo_url = "https://github.com/org/feature-module"
depends_on = ["common-lib"]

[[build-props]]
name = "DevSolution"
datatype = "boolean"
default = true
```

### Usage Examples

```bash
# Build all projects in dependency order
pace dotnet build

# Build projects starting from a specific project
pace --from ProjectName dotnet build

# Check git status across every repo
pace git status

# Run all unit tests and show a summary
pace test

# Format and verify code style
pace format --check
```

## License

[MIT](./LICENSE)
