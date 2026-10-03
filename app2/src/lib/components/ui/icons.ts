import sprite from "$lib/generated/calcite-icons.svg?raw";

/**
 * Icons are the Calcite UI icon set (https://developers.arcgis.com/calcite-design-system/icons/),
 * named as Calcite names them. `Icon` renders the app's selected subset from a
 * sprite that is bundled and added when this module first loads.
 *
 * The sprite and `IconName` are generated from the installed package by
 * scripts/generate-icons.js.
 */
export type { IconName } from "$lib/generated/icon-names";
import type { IconName } from "$lib/generated/icon-names";

/** Each icon is drawn separately at these sizes, rather than scaled */
export const iconSizes = [16, 24, 32] as const;
export type IconSize = (typeof iconSizes)[number];

/**
 * The drawing to use at a pixel size: the largest that isn't bigger than it, so
 * line weights stay close to the design (a 20px icon is the 16px drawing, scaled up).
 */
export function drawingFor(size: number): IconSize {
    return size >= 32 ? 32 : size >= 24 ? 24 : 16;
}

/**
 * Icons that point along the reading direction, so `Icon` mirrors them in
 * right-to-left layouts: "back" still points towards the start. (Calcite's own
 * components do the same with `flip-rtl`.)
 */
export const mirroredInRtl: ReadonlySet<IconName> = new Set<IconName>([
    "arrow-left",
    "arrow-right",
    "caret-left",
    "caret-right",
    "chevron-left",
    "chevron-right",
    "chevron-start",
    "chevron-end",
    "chevrons-left",
    "chevrons-right",
]);

/** The sprite symbol for an icon's drawing */
export function symbolId(name: IconName, drawing: IconSize) {
    return `icon-${name}-${drawing}`;
}

// Add the sprite once, outside the app's root, so it survives navigation and HMR.
if (
    typeof document !== "undefined" &&
    !document.getElementById("calcite-icon-sprite")
) {
    document.body.insertAdjacentHTML("afterbegin", sprite);
}
