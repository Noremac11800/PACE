#!/bin/bash

# Usage: ./generate-toml.sh [directory] [output.toml]
# Defaults: directory = current dir, output = projects.toml

DIR="${1:-.}"
OUTPUT="${2:-projects.toml}"

# Resolve to absolute path
DIR="$(cd "$DIR" && pwd)"

# Find all .csproj files recursively
declare -a csproj_files
while IFS= read -r -d '' file; do
    csproj_files+=("$file")
done < <(find "$DIR" -name "*.csproj" -print0 2>/dev/null)

if [ ${#csproj_files[@]} -eq 0 ]; then
    echo "No .csproj files found in $DIR"
    exit 1
fi

echo "Found ${#csproj_files[@]} project(s)"

# Write TOML header
> "$OUTPUT"
echo "repodir = \"$HOME/Documents/Development/dotnet\"" >> "$OUTPUT"
echo "nuget_cache_path = \"$HOME/custom-nuget-cache\"" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for csproj in "${csproj_files[@]}"; do
    # Get project name from parent directory name (matches how dotnet creates projects)
    proj_name=$(basename "$(dirname "$csproj")")
    
    # Get just the filename (not the full relative path)
    csproj_path=$(basename "$csproj")
    
    # Parse ProjectReference entries to extract dependency names
    declare -a deps
    if [ -f "$csproj" ]; then
        # Extract Include paths from ProjectReference elements
        while IFS= read -r line; do
            # Remove XML tags and get the Include value
            ref_path=$(echo "$line" | grep -o 'Include="[^"]*"' | sed 's/Include="//; s/"$//')
            if [ -n "$ref_path" ]; then
                # Normalize path separators and get parent directory name
                # e.g., "..\Lib0_abc123\Lib0_abc123.csproj" -> "Lib0_abc123"
                normalized_path=$(echo "$ref_path" | tr '\\' '/')
                dep_proj=$(basename "$(dirname "$normalized_path")")
                deps+=("$dep_proj")
            fi
        done < <(grep -o '<ProjectReference[^/]*/>' "$csproj" 2>/dev/null || true)
    fi
    
    # Derive sln_group from the project name prefix (before first underscore)
    sln_group=$(echo "$proj_name" | cut -d'_' -f1)
    [ -z "$sln_group" ] && sln_group="Default"

    # Write project entry to TOML
    echo "[[projects]]" >> "$OUTPUT"
    echo "name = \"$proj_name\"" >> "$OUTPUT"
    echo "csproj_path = \"$csproj_path\"" >> "$OUTPUT"
    echo "repo_url = \"\"" >> "$OUTPUT"
    echo "sln_group = \"$sln_group\"" >> "$OUTPUT"
    echo "explicit_frameworks = []" >> "$OUTPUT"
    
    # Write depends_on array
    if [ ${#deps[@]} -eq 0 ]; then
        echo "depends_on = []" >> "$OUTPUT"
    else
        echo -n "depends_on = [" >> "$OUTPUT"
        for ((i=0; i<${#deps[@]}; i++)); do
            if [ $i -gt 0 ]; then
                echo -n ", " >> "$OUTPUT"
            fi
            echo -n "\"${deps[$i]}\"" >> "$OUTPUT"
        done
        echo "]" >> "$OUTPUT"
    fi
    
    echo "" >> "$OUTPUT"
done

# Write well-known MSBuild build-props
cat >> "$OUTPUT" << 'EOF'

[[build-props]]
name = "GeneratePackageOnBuild"
datatype = "boolean"
default = false

[[build-props]]
name = "PackageOutputPath"
datatype = "path"
default = ""

[[build-props]]
name = "IncludeSymbols"
datatype = "boolean"
default = false

[[build-props]]
name = "SymbolPackageFormat"
datatype = "string"
default = "snupkg"

[[build-props]]
name = "TreatWarningsAsErrors"
datatype = "boolean"
default = false

[[build-props]]
name = "Nullable"
datatype = "string"
default = "enable"

[[build-props]]
name = "ImplicitUsings"
datatype = "string"
default = "enable"

[[build-props]]
name = "Optimize"
datatype = "boolean"
default = false

[[build-props]]
name = "DebugType"
datatype = "string"
default = "portable"

[[build-props]]
name = "AllowUnsafeBlocks"
datatype = "boolean"
default = false

[[build-props]]
name = "NoWarn"
datatype = "string"
default = ""

[[build-props]]
name = "AssemblyOriginatorKeyFile"
datatype = "path"
default = ""

[[build-props]]
name = "SignAssembly"
datatype = "boolean"
default = false

[[build-props]]
name = "PublishSingleFile"
datatype = "boolean"
default = false

[[build-props]]
name = "SelfContained"
datatype = "boolean"
default = false

[[build-props]]
name = "PublishReadyToRun"
datatype = "boolean"
default = false

[[build-props]]
name = "PublishTrimmed"
datatype = "boolean"
default = false

[[build-props]]
name = "InvariantGlobalization"
datatype = "boolean"
default = false

[[build-props]]
name = "RuntimeIdentifier"
datatype = "string"
default = ""

[[build-props]]
name = "BaseOutputPath"
datatype = "path"
default = ""

[[build-props]]
name = "BaseIntermediateOutputPath"
datatype = "path"
default = ""
EOF

echo "TOML file generated: $OUTPUT"
echo "Projects processed: ${#csproj_files[@]}"
