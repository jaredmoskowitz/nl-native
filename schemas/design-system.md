# Schema: Design System

Copy this template to `specs/changes/<change-name>/specs/core/design-system/<name>.md`.

The Visual Designer writes design system specs. They define appearance — exact visual tokens that both platform experts must follow. Every value must be concrete (hex codes, point sizes, milliseconds), never descriptions.

---

```markdown
# Design System: [Feature or Product Name]
Version: 1.0.0
Status: draft

## Overview

[One paragraph describing the visual identity this system defines. What product? What mood/aesthetic? What design philosophy?]

---

## 1. Color Tokens

### Semantic Palette

| Token | Light Mode | Dark Mode | Usage |
|---|---|---|---|
| background-primary | [hex] | [hex] | App background |
| background-elevated | [hex] | [hex] | Elevated surfaces (modals, sheets) |
| surface-card | [hex] | [hex] | Card backgrounds |
| text-primary | [hex] | [hex] | Primary text |
| text-secondary | [hex] | [hex] | Secondary text (subtitles) |
| text-muted | [hex] | [hex] | De-emphasized text (captions, hints) |
| text-on-action | [hex] | [hex] | Text on action-colored backgrounds |

### Action Palette

| Action | Start | End | Direction | Usage |
|---|---|---|---|---|
| [action-name] | [hex] | [hex] | [e.g., leading→trailing] | [when used] |

### Status Palette

| Token | Value | Usage |
|---|---|---|
| success | [hex] | Positive confirmations |
| warning | [hex] | Caution states |
| error | [hex] | Error states |
| info | [hex] | Informational states |

### Opacity Rules

| Situation | Opacity | Example |
|---|---|---|
| [context] | [0.0–1.0] | [when this applies] |

---

## 2. Typography Scale

### Scale

| Level | Size (pt) | Weight | Line Height | Usage |
|---|---|---|---|---|
| display | [pt] | [weight] | [multiplier] | Hero text, celebration |
| title | [pt] | [weight] | [multiplier] | Screen titles |
| headline | [pt] | [weight] | [multiplier] | Section headers, prominent labels |
| body | [pt] | [weight] | [multiplier] | Default content text |
| caption | [pt] | [weight] | [multiplier] | Supporting text, timestamps |
| label | [pt] | [weight] | [multiplier] | Badges, tags, buttons |

### Content Hierarchy

| Content Role | Scale Level | Weight Override | Color Token |
|---|---|---|---|
| [e.g., sender name] | [e.g., headline] | [e.g., bold] | [e.g., text-primary] |

### Platform Font Mapping

| Platform | Typeface | Notes |
|---|---|---|
| iOS | SF Pro Display | System default, respects Dynamic Type |
| Android | System default (Roboto) | Or Inter if specified. Respects text size settings. |

Sizes and weights are shared. Typeface is native.

---

## 3. Spacing & Layout

### Base Unit

[e.g., 4pt]

### Scale

| Name | Value | Usage |
|---|---|---|
| xs | [e.g., 4pt] | Tight gaps (badge padding, icon margins) |
| sm | [e.g., 8pt] | Small gaps (between related elements) |
| md | [e.g., 16pt] | Standard gaps (section spacing) |
| lg | [e.g., 24pt] | Large gaps (card padding, screen margins) |
| xl | [e.g., 32pt] | Extra-large (between major sections) |
| xxl | [e.g., 48pt] | Maximum spacing |

### Component Spacing

| Component | Property | Value |
|---|---|---|
| [e.g., email-card] | [e.g., inner-padding] | [e.g., lg (24pt)] |

---

## 4. Shape & Elevation

### Corner Radii

| Element | Radius | Notes |
|---|---|---|
| card | [pt] | |
| button | [pt] | |
| badge | [pt] | |
| avatar | full (circle) | |
| input | [pt] | |
| toast | [pt] | |

### Elevation / Shadow

| Level | Offset X | Offset Y | Blur | Spread | Color | Opacity |
|---|---|---|---|---|---|---|
| card | [pt] | [pt] | [pt] | [pt] | [hex] | [0.0–1.0] |
| toast | [pt] | [pt] | [pt] | [pt] | [hex] | [0.0–1.0] |

### Borders

| Element | Thickness | Color |
|---|---|---|
| divider | [pt] | [hex + opacity] |

---

## 5. Component Specs

### [Component Name]

**Anatomy:**
[Describe the exact layout: element order, alignment, sizing]

| Sub-element | Size | Position | Spacing from adjacent |
|---|---|---|---|
| [e.g., avatar] | [e.g., 48pt circle] | [e.g., left-aligned] | [e.g., 12pt right gap] |

**Constraints:**
- Min height: [pt]
- Max lines before truncation: [number per text element]

[Repeat for each shared component]

---

## 6. Animation & Motion

### Spring Parameters

| Context | Damping Ratio | Stiffness | Notes |
|---|---|---|---|
| [e.g., card snap-back] | [e.g., 0.7] | [e.g., 400] | |

### Timing

| Animation | Duration | Easing | Notes |
|---|---|---|---|
| [e.g., card dismiss] | [e.g., 200–400ms] | [e.g., velocity-based] | |

### Formulas

| Effect | Formula | Notes |
|---|---|---|
| [e.g., color bleed opacity] | [e.g., min(abs(offset) / 150, 0.6)] | Same on both platforms |

### Thresholds

| Threshold | Value | Notes |
|---|---|---|
| [e.g., swipe dismiss] | [e.g., 150pt distance OR 500pt/s velocity] | |

---

## Platform-Native Elements (NOT specified here)

- Icon set: platform-native (SF Symbols / Material Icons)
- System typeface: platform-native (sizes and weights from this spec)
- Navigation patterns: platform conventions
- Gesture conventions: platform conventions
- Status bar / system chrome: platform conventions

---

## Changelog

| Version | Change | Date |
|---|---|---|
| 1.0.0 | Initial design system | [date] |
```

---

## Writing good design tokens

**Exact:** `#0f0f1a` not "very dark blue". `16pt` not "medium spacing". `300ms` not "quick animation".

**Semantic:** Name tokens by purpose (`background-primary`) not by value (`dark-navy`). The value can change; the purpose is stable.

**Complete:** If a component appears on both platforms, every visual property must be specified. An unspecified property is an invitation for divergence.

**Testable:** A QA verifier must be able to compare a platform's implementation against each token and say pass/fail. If a token is too vague to verify, make it more specific.
