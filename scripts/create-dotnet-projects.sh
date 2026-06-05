#!/bin/bash

# Usage: ./create-dotnet-projects.sh [N] [S]
#   N = number of projects (default 10)
#   S = number of solution groups (default 3)

DIR="$HOME/Documents/Development/dotnet"
N=${1:-10}
S=${2:-3}

# Solution group names pool (picks first S)
ALL_GROUP_NAMES=(
    "Foundation"
    "Core"
    "Services"
    "Infrastructure"
    "Application"
    "Integration"
    "Utilities"
    "Presentation"
)

# Clamp S to available group names
MAX_GROUPS=${#ALL_GROUP_NAMES[@]}
if [ "$S" -gt "$MAX_GROUPS" ]; then
    S=$MAX_GROUPS
fi

# Build the active group list
declare -a GROUP_NAMES
for ((g=0; g<S; g++)); do
    GROUP_NAMES+=("${ALL_GROUP_NAMES[$g]}")
done

# Clear or create directory
if [ -d "$DIR" ]; then
    echo "Clearing $DIR..."
    rm -rf "$DIR"/*
else
    echo "Creating $DIR..."
    mkdir -p "$DIR"
fi

cd "$DIR"

# Assign each project index to a layer (0 = lowest/foundation, S-1 = highest)
# Projects are distributed across layers roughly evenly
declare -a project_layer   # layer index per project
declare -a project_group   # group name per project
declare -a projects

echo "Creating $N class libraries across $S solution group(s): ${GROUP_NAMES[*]}"
echo ""

for ((i=0; i<N; i++)); do
    random_suffix=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 6 | head -n 1)
    # Assign layer: spread projects across layers in order
    layer=$(( (i * S) / N ))
    group="${GROUP_NAMES[$layer]}"
    proj_name="${group}_${random_suffix}"
    projects+=("$proj_name")
    project_layer+=($layer)
    project_group+=("$group")

    echo "  Creating $proj_name (group: $group)..."
    dotnet new classlib -n "$proj_name" -o "$proj_name" --no-restore

    if [ $? -ne 0 ]; then
        echo "Error creating project $proj_name"
        exit 1
    fi
done

echo ""
echo "Projects created: ${projects[*]}"
echo ""

# ---------------------------------------------------------------------------
# Build dependency graph with transitive normalisation
#
# Rules:
#   - At most MAX_ROOTS root nodes (layer 0 projects with no dependencies)
#   - Each project references at most MAX_DIRECT_DEPS direct dependencies
#   - Candidates are weighted heavily toward the immediately lower layer to
#     keep the tree tall rather than wide (skip-layer refs only as fallback)
#   - Redundant direct refs (already reachable transitively) are pruned
# ---------------------------------------------------------------------------

MAX_ROOTS=3
MAX_DIRECT_DEPS=4

# direct_deps[i] = space-separated list of project indices that i directly depends on
declare -a direct_deps
for ((i=0; i<N; i++)); do
    direct_deps[$i]=""
done

# BFS reachability check: returns 0 if $2 is reachable from $1 via direct_deps
is_transitive_reachable() {
    local from=$1
    local target=$2
    local -a queue=()
    local -A visited=()

    for dep in ${direct_deps[$from]}; do
        queue+=($dep)
    done

    while [ ${#queue[@]} -gt 0 ]; do
        local node=${queue[0]}
        queue=("${queue[@]:1}")
        [ "${visited[$node]+_}" ] && continue
        visited[$node]=1
        if [ "$node" -eq "$target" ]; then
            return 0
        fi
        for dep in ${direct_deps[$node]}; do
            queue+=($dep)
        done
    done
    return 1
}

# Count how many layer-0 projects will be roots (no deps assigned)
# Reserve slots: only the first MAX_ROOTS layer-0 projects are roots;
# the rest must depend on an already-rooted layer-0 project.
root_count=0

echo "Adding project references (normalised dependency tree)..."
for ((i=0; i<N; i++)); do
    current_layer=${project_layer[$i]}

    # Layer 0: decide if this project is a root or must depend on an earlier layer-0 root
    if [ "$current_layer" -eq 0 ]; then
        if [ "$root_count" -lt "$MAX_ROOTS" ]; then
            root_count=$((root_count + 1))
            # No deps — this is a root
            direct_deps[$i]=""
        else
            # Must depend on one of the existing roots (earlier layer-0 projects)
            layer0_roots=()
            for ((j=0; j<i; j++)); do
                if [ "${project_layer[$j]}" -eq 0 ] && [ -z "${direct_deps[$j]}" ]; then
                    layer0_roots+=($j)
                fi
            done
            if [ ${#layer0_roots[@]} -gt 0 ]; then
                pick=${layer0_roots[$((RANDOM % ${#layer0_roots[@]}))]}
                direct_deps[$i]="$pick"
                current_proj="${projects[$i]}"
                dep_proj="${projects[$pick]}"
                echo "  $current_proj -> $dep_proj"
                dotnet add "$DIR/$current_proj/$current_proj.csproj" reference "$DIR/$dep_proj/$dep_proj.csproj"
            fi
        fi
        continue
    fi

    # For non-root layers: prefer candidates from the immediately lower layer,
    # fall back to any lower layer only if the adjacent layer is empty.
    adjacent_layer=$((current_layer - 1))
    adjacent_candidates=()
    all_lower_candidates=()
    for ((j=0; j<i; j++)); do
        jlayer=${project_layer[$j]}
        if [ "$jlayer" -lt "$current_layer" ]; then
            all_lower_candidates+=($j)
            [ "$jlayer" -eq "$adjacent_layer" ] && adjacent_candidates+=($j)
        fi
    done

    # Use adjacent layer if available; otherwise fall back to all lower
    if [ ${#adjacent_candidates[@]} -gt 0 ]; then
        pool=("${adjacent_candidates[@]}")
    else
        pool=("${all_lower_candidates[@]}")
    fi

    [ ${#pool[@]} -eq 0 ] && continue

    # Pick 1..MAX_DIRECT_DEPS from pool
    max_pick=$((${#pool[@]} < MAX_DIRECT_DEPS ? ${#pool[@]} : MAX_DIRECT_DEPS))
    num_pick=$((1 + RANDOM % max_pick))
    chosen=($(printf '%s\n' "${pool[@]}" | shuf | head -n $num_pick))

    # Normalise: prune deps already reachable transitively through another chosen dep
    direct_deps[$i]="${chosen[*]}"
    normalised=()
    for dep in "${chosen[@]}"; do
        redundant=0
        for other in "${chosen[@]}"; do
            [ "$other" -eq "$dep" ] && continue
            saved_deps="${direct_deps[$i]}"
            direct_deps[$i]="$other"
            if is_transitive_reachable "$i" "$dep"; then
                redundant=1
            fi
            direct_deps[$i]="$saved_deps"
            [ "$redundant" -eq 1 ] && break
        done
        [ "$redundant" -eq 0 ] && normalised+=($dep)
    done

    # Ensure at least one dep remains
    [ ${#normalised[@]} -eq 0 ] && normalised=("${chosen[0]}")

    direct_deps[$i]="${normalised[*]}"

    current_proj="${projects[$i]}"
    current_csproj="$DIR/$current_proj/$current_proj.csproj"

    for dep_idx in "${normalised[@]}"; do
        dep_proj="${projects[$dep_idx]}"
        dep_csproj="$DIR/$dep_proj/$dep_proj.csproj"
        echo "  $current_proj -> $dep_proj"
        dotnet add "$current_csproj" reference "$dep_csproj"
        if [ $? -ne 0 ]; then
            echo "Error adding reference from $current_proj to $dep_proj"
            exit 1
        fi
    done
done

echo ""
echo "Done! Created $N class libraries in $DIR across solution groups: ${GROUP_NAMES[*]}"
echo ""
echo "Dependency summary:"
for ((i=0; i<N; i++)); do
    proj_name="${projects[$i]}"
    group="${project_group[$i]}"
    deps_str="${direct_deps[$i]}"
    if [ -z "$deps_str" ]; then
        echo "  [$group] $proj_name: (root)"
    else
        dep_names=()
        for dep_idx in $deps_str; do
            dep_names+=("${projects[$dep_idx]}")
        done
        echo "  [$group] $proj_name: depends on ${dep_names[*]}"
    fi
done
