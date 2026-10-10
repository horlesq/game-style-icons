---
name: Game Style Icons
description: The instruction booklet in the box, printed on white coated paper in black ink plus one spot ink per world.
colors:
  spot-ink: "#e02420"
  on-ink: "#ffffff"
  paper: "#fdfdfb"
  press-black: "#121212"
  muted-ink: "#4a4a46"
  hairline-rule: "rgba(18, 18, 18, .16)"
  screen: "#111216"
  screen-text: "#e9ebee"
  screen-muted: "#9aa0a8"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(3.4rem, 8.4vw, 6rem)"
    fontWeight: 900
    lineHeight: 0.92
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 125"
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(2.2rem, 5.4vw, 4.2rem)"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.005em"
    fontVariation: "'wdth' 125"
  lede:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(1.25rem, 2.2vw, 1.6rem)"
    fontWeight: 800
    lineHeight: 1.2
    fontVariation: "'wdth' 112"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 800
    lineHeight: 1.2
    fontVariation: "'wdth' 112"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.02em"
  numeral:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 900
    fontFeature: "'tnum'"
    fontVariation: "'wdth' 125"
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.88rem"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  folio: "6px"
  step: "8px"
  tab: "10px"
  tile: "12px"
  screen: "14px"
  item-box: "22px"
  pill: "999px"
spacing:
  gutter: "clamp(16px, 4.5vw, 64px)"
  tab-rail: "58px"
  page-pad: "clamp(28px, 4vw, 56px)"
  band-pad: "clamp(18px, 3vw, 30px)"
  page-foot: "96px"
components:
  button:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.press-black}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 18px"
    height: "46px"
  button-hover:
    backgroundColor: "{colors.press-black}"
    textColor: "{colors.paper}"
  button-primary:
    backgroundColor: "{colors.press-black}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "0 18px"
    height: "46px"
  button-primary-hover:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.press-black}"
  page-tab:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.press-black}"
    rounded: "{rounded.tab}"
    width: "{spacing.tab-rail}"
  page-tab-current:
    backgroundColor: "{colors.spot-ink}"
    textColor: "{colors.on-ink}"
  folio:
    backgroundColor: "{colors.press-black}"
    textColor: "{colors.paper}"
    typography: "{typography.numeral}"
    rounded: "{rounded.folio}"
    height: "34px"
  code-block:
    backgroundColor: "{colors.press-black}"
    textColor: "{colors.paper}"
    typography: "{typography.code}"
    rounded: "{rounded.tab}"
    padding: "16px 18px"
  screen-frame:
    backgroundColor: "{colors.screen}"
    textColor: "{colors.screen-text}"
    rounded: "{rounded.screen}"
    padding: "24px"
  input-field:
    backgroundColor: "#ffffff"
    textColor: "{colors.press-black}"
    rounded: "{rounded.tile}"
    padding: "0 16px"
    height: "50px"
  tile:
    backgroundColor: "transparent"
    textColor: "{colors.press-black}"
    rounded: "{rounded.tile}"
    padding: "14px 6px 10px"
  tile-selected:
    backgroundColor: "{colors.spot-ink}"
    textColor: "{colors.on-ink}"
---

# Design System: Game Style Icons

## Overview

**Creative North Star: "The Cartridge Manual"**

The page is printed like the instruction booklet that came in a 90s game box: bright white coated paper, black ink, and one spot ink per edition. The spot ink is not a brand colour; it belongs to whichever world (style) the reader has chosen, Super Mario red by default, and every inked surface shares it. Pick a different world and the whole booklet is reprinted in that world's ink with a single wipe.

Structure comes from print furniture rather than web chrome: chapter bands in spot ink with a halftone dot screen, two-page spreads with a soft gutter shadow down the middle, numbered page tabs on the edge, folios in the page corners, and dark captioned "Fig." screens wherever icons sit on dark. Type is Archivo pushed to its widest axis in black caps for titles, plain Archivo for reading, and JetBrains Mono only for code. The icons themselves supply all illustration; even the interface glyphs (copy, star, flag, download) are drawn from the package, in the current world.

Density is a manual's: generous page padding, short measure, clear numbered steps, tables with hairline rules. Ornament is limited to what a printer would have: dot screens, double rules, rivet dots, numbered blocks.

**Key Characteristics:**
- One variable spot ink (`--ink` / `--on-ink`) drives every coloured surface; everything else is paper and black.
- Archivo at width 125, weight 900, uppercase for every title; tabular numerals for every number that counts pages or levels.
- Dark "screens" are the only dark surfaces besides black type plates, and they always carry icons.
- Thick black strokes (2px for controls, 3-4px for frames) define shape; shadow is rare.
- Motion is two things only: the cover item stepping through worlds and the re-ink wipe.

## Colors

Paper and press black do all the work; one spot ink, swapped per world, is the only colour.

### Primary
- **Spot Ink** (default Super Mario red): cover field, chapter bands, the current page tab, the selected world row, the selected item tile, selection highlight, and the A button on the drawn controller. It is a runtime variable: each world ships its own ink and a paired text colour (`on-ink`, either white or press black, chosen per ink for contrast). Never hard-code a world's hex into a component; reference the ink.
- **On-Ink** (white by default; press black for light inks): text and folios set on spot ink. On the cover the folio inverts to on-ink ground with ink numerals.

### Neutral
- **Coated Paper** (near-white, faintly warm): page ground, button ground, page tab ground.
- **Press Black**: all type, every stroke and border, folios, code plates, primary buttons, the selected install tab.
- **Muted Ink** (warm dark grey): captions, secondary text, counts beside headings, table column heads.
- **Hairline Rule** (black at 16%): page divider between left and right pages, table rules, the inspector edge.
- **Screen** (blue-black): "Fig." screens, level strips and the every-world grid, where icons are shown on dark.
- **Screen Text / Screen Muted**: text and hover outlines inside screens.

### Named Rules
**The One Spot Ink Rule.** A spread prints in paper, black and exactly one spot ink, the current world's. No second accent, no gradients between inks. A selected state is shown by filling with the spot ink and keeping a black border.

**The Ink Is a Variable Rule.** Spot ink and its text colour always travel together as a pair from the world data; a surface that takes `--ink` as background takes `--on-ink` as text, never a fixed white.

## Typography

**Display Font:** Archivo variable (wdth 62-125, wght 100-900), self-hosted, with system-ui fallback
**Body Font:** Archivo at normal width
**Label/Mono Font:** JetBrains Mono, code only

**Character:** One grotesque family stretched between two voices: expanded black caps that shout like a box cover, and a plain normal-width text face that explains like the manual's body copy. Mono appears only where the reader will copy something.

### Hierarchy
- **Display** (900, width 125, uppercase, clamp 3.4-6rem, 0.92): the cover title only.
- **Headline** (900, width 125, uppercase, clamp 2.2-4.2rem, 1): chapter band titles.
- **Lede** (800, width 112, clamp 1.25-1.6rem, 1.2): the cover's one-line promise.
- **Title** (800, width 112, 1.35rem, 1.2): step titles and sub-heads. Section heads inside a page (world categories, item groups, the inspector title, the warning plate) step up to width 125, 900, uppercase.
- **Body** (400, 1.0625rem, 1.55): reading text, held to 52-72ch; intros at 1.1rem.
- **Label** (700, 0.8-0.95rem): buttons, tabs, table heads (uppercase, +0.04em), page-tab names (uppercase, +0.02em, set vertically on desktop).
- **Numeral** (900, width 125, tabular): page-tab numbers, folios, step counters, world-level numbers.
- **Code** (JetBrains Mono 400-500, 0.88-0.95rem, 1.6): install lines, import snippets, component names, the repo path.

### Named Rules
**The Expanded Caps Rule.** Every title that names a page, chapter or section is Archivo at width 125, weight 900, uppercase. Body copy never uses the expanded width.

**The Mono Means Copyable Rule.** JetBrains Mono is used only for code and identifiers the reader can paste. Never for labels, captions or decoration.

## Layout

The page is a booklet read top to bottom: a full-viewport cover, then chapters. Each chapter is a spread: a full-width spot-ink band carrying the chapter title, then two equal pages side by side, divided by a hairline and a soft gutter shading (black at 5.5%, fading over 26px either side of the centre). Long chapters (Worlds) run as a single flowing page; the Items chapter splits 1.25 : 0.75 with a sticky inspector on the right.

Horizontal padding is a fluid gutter (16-64px) on the left and gutter plus the 58px page-tab rail on the right, so content never runs under the tabs. Page padding is 28-56px top and 96px bottom, leaving room for the folio. Below 1080px the two-column grids (worlds, items) collapse to one column and the inspector moves above the list. Below 860px spreads stack into single pages separated by a dashed hairline, the page tabs move to a bottom bar, and the cover stacks title, item box (small, beside its caption) and text.

## Elevation & Depth

Flat print. Depth comes from ink, not light: black plates, dark screens, thick strokes and halftone. Two shadows exist and both are physical metaphors.

### Shadow Vocabulary
- **Box lift** (`box-shadow: 0 18px 40px -16px rgba(0, 0, 0, .45)`): only under the cover item box, the one object that sits on the cover like a cartridge.
- **Screen bezel** (`box-shadow: inset 0 0 0 3px #000, inset 0 0 48px rgba(255, 255, 255, .04)`): inside every dark screen, a black bezel and faint glass glow.
- **Ink ring** (`box-shadow: 0 0 0 3px paper, 0 0 0 5px spot ink`): a paper gap then a spot-ink ring around numbered step blocks.

### Named Rules
**The Printed, Not Lit Rule.** Surfaces do not float. Use a black border, a spot-ink fill or a dark screen to separate things; the box lift is reserved for the cover item box.

## Shapes

Softly rounded rectangles under heavy black strokes. Controls are pills (999px); tabs are rounded on the outer side only (10px), like die-cut index tabs; tiles and fields 12px; screens and cards 14px; the item box 22px with a 4px stroke and four rivet dots inset 14px in its corners. Folios are small 6px-rounded black blocks; step numbers 8px-rounded black squares. The warning panel is the one square-ish form: a 7px double rule with a black title plate. Stroke weights: 2px for controls, tabs, tiles and spreads; 3px for world-category underlines and the mobile tab bar; 4px for the item box.

## Components

### Buttons
Pills with a black stroke; they invert on hover.
- **Shape:** full pill (999px), 2px press-black border, 46px min height, 18px side padding, label type, icon 20px with 9px gap.
- **Default:** paper ground, black text; hover fills black with paper text.
- **Primary:** black ground, paper text; hover inverts to paper. Inside a black plate (the install slot) the primary flips to paper, and hovers to spot ink.
- **Active:** 1px press down. Text links are 2px underlines at 0.2em offset.

### Chips
- **Level tag** (world-level number beside a world name): on-ink ground, ink numerals, 5px radius, numeral type at 0.7em.

### Cards / Containers
- **Code plate:** press-black ground, near-white mono text, 10px radius, 16px 18px padding. Keywords take the spot ink (or a light coral when the ink is too dark to read on black); strings green, types blue, comments screen-muted.
- **Screen ("Fig."):** screen ground, 14px radius, bezel shadow, always followed by a caption beginning with a bold "Fig. n".
- **Item card views:** paper square with a 2px black stroke and 14px radius beside a dark screen square, the same icon on both grounds.

### Inputs / Fields
- **Style:** white ground, 2px black border, 12px radius, 50px min height, label in 800 width-112 above.
- **Focus:** 3px spot-ink outline at 2px offset. Global focus elsewhere is a 3px press-black outline at 3px offset.

### Navigation
- **Page tabs:** the only navigation. Fixed to the right edge, vertically centred; each tab is 58px wide, paper with a 2px black border open on the right, a tabular page number above a vertical uppercase name. Hover slides it 4px out; the current page fills with spot ink. Below 860px they become an equal-width bottom bar with a 2px top rule and horizontal names.
- **Folios:** page numbers in black blocks at the bottom corners of each page.

### Selection tiles (world rows, item tiles)
Transparent with a 2px transparent border at rest; hover shows the black border; selected fills with spot ink, on-ink text, black border. World rows carry a dark level strip of sample icons; the selected row adds a "Your world" flag.

### Item Box (signature)
The cover's hero object: a paper square with a 4px black stroke, 22px radius, rivet dots in the corners and the box lift shadow, holding one icon at 62% that steps through every world every 1.4s (still under reduced motion), captioned with the world name and level tag.

### Re-ink Wipe (signature)
Choosing a world wipes the new spot ink across every inked band left to right (0.6s, `cubic-bezier(.16, 1, .3, 1)`), then commits it. Bands carry a 7px halftone dot screen (black at 20%) masked to fade in from the left. Reduced motion swaps instantly.

## Do's and Don'ts

### Do:
- **Do** take every coloured fill from the spot ink pair (`--ink` with `--on-ink`) so a world change reprints it.
- **Do** set page, chapter and section titles in Archivo width 125, weight 900, uppercase, and every counting number in tabular numerals.
- **Do** show icons on both paper and a dark screen, and caption dark screens with "Fig. n".
- **Do** draw interface glyphs from the package itself, in the current world.
- **Do** separate surfaces with 2px black strokes, hairline rules and spot-ink fills before reaching for shadow.
- **Do** keep motion to the cover stepper and the re-ink wipe, and hold both still under reduced motion.

### Don't:
- **Don't** introduce a second accent colour or a fixed brand colour beside the spot ink.
- **Don't** use JetBrains Mono for anything that is not code or a copyable identifier.
- **Don't** add drop shadows to cards, buttons or tiles; the box lift belongs to the cover item box alone.
- **Don't** use game logos, characters, official artwork or game fonts anywhere on the page.
- **Don't** add navigation beyond the page tabs.
