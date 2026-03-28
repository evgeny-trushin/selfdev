# Increment 0017: Visual Debug Mode for UI Testing and Debugging

**Requirement ID:** R17
**Status:** TODO

## Description

Implement a toggleable visual debug overlay for UI testing and debugging. The overlay must render color-coded borders on UI elements so developers can quickly identify layout issues, component boundaries, hierarchy violations, and common rendering/accessibility problems.

The overlay is intended for use in UI tests and live debugging sessions, and must be framework-agnostic.

### Border Combination Matrix

Use a matrix of **10 colors x 4 line types x 2 line widths = 80 unique border combinations**.

No two element categories may share the same **color + line type + line width** combination at the same time.

#### Line Type Assignment

| Line Type | Assigned To |
|---|---|
| **Dotted** | Interactive elements: buttons, inputs, links, toggles, sliders, dropdowns |
| **Double** | Interactive containers: forms, modals, dialogs, menus, toolbars |
| **Solid** | Static elements: headings, paragraphs, images, icons, dividers |
| **Dashed** | Informational elements: tooltips, badges, alerts, status indicators, labels |

#### Line Width Assignment

| Line Width | Assigned To |
|---|---|
| **Thick (3px-4px)** | Small elements, to ensure visibility on compact targets |
| **Thin (1px-2px)** | Large elements, to avoid visual noise on spacious containers |

#### Color Palette

| # | Color | Hex |
|---|---|---|
| 1 | Red | `#FF0000` |
| 2 | Orange | `#FF8C00` |
| 3 | Lime Green | `#00FF00` |
| 4 | Cyan | `#00FFFF` |
| 5 | Yellow | `#FFFF00` |
| 6 | Magenta | `#FF00FF` |
| 7 | Blue | `#4488FF` |
| 8 | White (0.4 opacity) | `rgba(255,255,255,0.4)` |
| 9 | Bright Green | `#39FF14` |
| 10 | Bright Red | `#FF3333` |

Color assignment is implementation-specific as long as combinations remain unique and high contrast in both light and dark themes.

### Functional Requirements

- Borders must not affect layout. Use non-layout-impacting rendering.
- Hover and focus tooltip must display:
  - element type
  - dimensions
  - padding
  - margin
  - position
  - z-index
  - legend label
- Provide depth-level filtering:
  - Level 1: containers only
  - Level 2: containers plus wrappers
  - Level 3: all elements
  - Custom: selector-based filtering
- Auto-flag problem elements:
  - overflow clipping
  - z-index greater than `9999`
  - zero-dimension parents
  - missing accessible names
- Include a floating draggable legend panel showing all active combinations.
- Toggle on and off without page reload.
- Activation should complete in under `100ms` on views containing `2000+` elements.

## Related Principles

- [UIX — UI State Coverage](../principles/UIX.md)
- [DTL — Detail Fidelity](../principles/DTL.md)
- [NSF — Next-State Feedback](../principles/NSF.md)
- [G2 — Actionable](../principles/G2.md)
- [G4 — Measurable](../principles/G4.md)
- [SYS — System Perspective](../principles/SYS.md)
- [DBG — Debug Perspective](../principles/DBG.md)
- [M3 — Transparency](../principles/M3.md)

## Acceptance Criteria

- [ ] Toggle on and off without reload
- [ ] Every element category has a unique combination from the 80-type matrix
- [ ] Line types are correctly assigned: dotted=interactive, double=interactive containers, solid=static, dashed=informational
- [ ] Line widths are correctly assigned: thick=small elements, thin=large elements
- [ ] Debug borders cause zero layout shift
- [ ] Hover and focus tooltips show the required metadata
- [ ] Problem elements are auto-flagged
- [ ] Legend panel is draggable and reflects active combinations
- [ ] Depth filtering works for Level 1, Level 2, Level 3, and custom selector-based mode
- [ ] Activation remains under 100ms on 2000+ element views
- [ ] Implementation is framework-agnostic with no platform dependency
