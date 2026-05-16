# Color palette system

This document explains the color design logic used across instance themes, why those choices work, and how to select a well-formed palette for future versions.

_Claude was used to iterate on a color palette for the Canada instance, and this documentation was written with them. Thank you!_

---

## How colors are used in the app

Three CSS variables drive the entire visual theme:

```css
:root {
  /* navbar background, page titles, body links, card headers, pagination active */
  --primary-color:
  /* navbar hover states, subtitles, category titles */
  --secondary-color:
  /* h4 headings — currently unused */
  --tertiary-color:
}
```

Because `--primary-color` appears in large areas (the full navbar) and at high frequency (every link on every page), it needs to be a color you can look at for extended periods.

Because `--secondary-color` appears in accent roles (hover states, subtitles), it can carry more visual energy — that's actually what makes it work.

---

## Current themes

### Base / Dana-Farber

```css
:root {
    --primary-color: #00629B;   /* Dana-Farber Blue */
    --secondary-color: #FFA300; /* Dana-Farber Orange */
    --tertiary-color: #41B6E6;  /* Dana-Farber Light Blue */
}
```

### Ireland / University of Limerick

```css
:root {
    --primary-color: #005335;   /* University of Limerick Green */
    --secondary-color: #FFA300; /* Golden Leaf */
    --tertiary-color: #003726;  /* University of Limerick Heritage Green */
}
```

### Canada / Institute for Cancer Research inspired

```css
:root {
    --primary-color: #006070;   /* Dark Teal */
    --secondary-color: #F09500; /* Amber */
    --tertiary-color: #3A9BAD;  /* Lighter tint of primary */
}
```

---

## Why these palettes work: the underlying color theory

All three themes follow the same structural logic, arrived at independently but grounded in how human vision processes color. There are two principles at work simultaneously.

### 1. Warm vs. cool hue contrast

The color wheel divides into warm colors (reds, oranges, yellows — roughly 0–60° and 330–360°) and cool colors (greens, blues, teals — roughly 90–270°). All three primary colors sit in the cool half of the wheel:

| Theme         | Primary hue   | Approx. wheel position |
|---------------|---------------|------------------------|
| Dana-Farber   | Azure blue    | ~207°                  |
| Limerick      | Forest green  | ~153°                  |
| Canada / ICR  | Dark teal     | ~185°                  |

All three secondary colors are amber-orange, sitting at roughly 35–40° — firmly in the warm half. When a warm and cool color appear together, the eye immediately reads them as distinct categories. This separation happens before conscious processing, which is why interactive states (hover, subtitles) feel immediately legible as "different" from structural elements (navbar, links, titles) without the reader having to think about it.

This warm/cool contrast is also what makes these palettes robust for colorblind users. Red-green colorblindness (affecting ~8% of men) confuses hues along the red-green axis. Warm-vs-cool contrast survives almost all forms of colorblindness because it relies on brightness and temperature cues, not hue discrimination alone. Pairing a red primary with a green secondary — as an earlier Canada draft did — would be a problem. Pairing any cool primary with an amber-orange secondary avoids it entirely.

### 2. Value (lightness) contrast

Hue contrast alone is not enough. The second axis is lightness — how dark or light a color is on a scale of 0–100%. The primaries and secondaries in these themes sit at very different points on that scale:

| Theme        | Primary lightness | Secondary lightness | Gap    |
|--------------|-------------------|---------------------|--------|
| Dana-Farber  | ~30%              | ~66%                | ~36 pts |
| Limerick     | ~20%              | ~66%                | ~46 pts |
| Canada / ICR | ~23%              | ~63%                | ~40 pts |

A gap of roughly 35–46 lightness points means that even in grayscale, the primary and secondary read as visually distinct — the primary would be a dark gray, the secondary a mid-tone. This is what gives hover states their "pop" and makes subtitle text feel subordinate but present. When the gap is too small (below ~30 points), the two colors feel like neighbors rather than a deliberate system, and interactive states lose their signal.

### 3. Why amber specifically

Orange-amber at 35–40° on the color wheel sits nearly opposite the blue-teal range (180–210°). Colors that are opposite on the wheel are called complementary pairs — they create maximum hue contrast with each other. All three cool primaries are close enough to the blue-teal range that amber reads as the natural complement.

Amber also occupies a functional sweet spot on the warm spectrum:

- **Too yellow (50–60°):** starts to read as a warning color — clinical, alarming
- **35–40° (amber):** warm and inviting, high visibility against dark surfaces, no negative connotations
- **Too orange-red (15–25°):** begins to feel hot and aggressive; approaches the red territory that creates colorblind and fatigue problems

Amber is also one of the highest-contrast warm colors against dark cool backgrounds, which is why it appears on road signs, construction equipment, and safety markings — it is essentially designed by decades of applied use to be noticed without being harsh.

`#FFA300` is full-saturation amber — 100% saturation in HSL — which is why it works identically as a secondary against both the Dana-Farber navy and the Limerick forest green. `#F09500` pulls saturation back slightly and reduces lightness a touch (landing at ~63% rather than ~66%), which takes a small amount of edge off. Against a teal primary — which carries more visual complexity than a pure navy or green, sitting between blue and green on the wheel — this fractional reduction lets the primary breathe slightly more. The difference is subtle; both are valid choices.

---

## How to choose a palette for a future institutional theme

If you are adding a new version of MOAlmanac for a partner institution and need to choose colors, follow these steps.

### Step 1: Identify the institutional hue

Start from the institution's brand colors. Pick the one that:

- Is most closely associated with the institution
- Is on the cool side of the color wheel (blues, greens, teals, or blue-purples)

If the institution's primary color is warm (red, orange, yellow), do not use it directly as `--primary-color`. It will be fatiguing at navbar scale and as body link color. Instead, look at secondary brand colors for a cooler option, or find a cool color that is associated with the institution's geography or identity.

### Step 2: Darken and desaturate to a usable primary

Institutional brand colors are designed for logos and print — they are often too saturated or too bright for large UI surfaces. A good `--primary-color` should have:

- **Lightness: 18–32%** — dark enough to feel anchored, light enough to still read as the institution's hue
- **Saturation: 50–90%** — still clearly a color, but not a pure saturated tone
- **Hue: in the cool half of the wheel** — roughly 90–270°

To move from a bright brand color to a usable primary, keep the hue the same and reduce lightness to the target range. Most color pickers (CSS, Figma, etc.) will let you adjust HSL values directly.

Example: ICR's brand green is `#65bc45` (HSL: 103°, 53%, 50%). Keeping the hue at ~103° and pulling lightness down to ~25% and adjusting saturation gives `#2E6B1A` — still clearly green, but usable as a navbar background.

### Step 3: Check the hue angle against the amber range

Your primary hue (step 1) should sit between roughly 90° and 270° on the color wheel. The further it is from 35–40° (amber), the stronger the warm/cool contrast will be. Anything in the 150–220° range (greens, teals, blues) will pair naturally with amber. Hues closer to 90° (yellow-green) or 270° (blue-violet) will still work but with slightly less dramatic contrast.

### Step 4: Choose a secondary

The secondary should be warm and lighter than the primary. Start with `#FFA300` (full amber) and adjust based on the primary:

- **If the primary is very dark (lightness < 22%):** `#FFA300` at full saturation is appropriate — the value gap is large enough. This is the Limerick case.
- **If the primary is mid-dark (lightness 22–32%):** `#F09500` or `#E08C00` give a slightly quieter secondary that avoids competing with the primary. This is the Canada/ICR case.
- **If the secondary feels too yellow** against your specific primary, shift it slightly toward orange — move the hue from 38° toward 30°, keeping saturation and lightness fixed.
- **If the secondary feels too muted** as subtitle text on a white background, increase lightness slightly — but keep it below ~68% to maintain readability.

The target value gap between primary and secondary lightness is **35–46 points**. Below 30, the colors feel too similar in weight. Above 50, the secondary starts to feel unmoored from the palette.

### Step 5: Choose a tertiary (if needed)

Currently `--tertiary-color` is not independently used — h4 elements also carry the `.subtitle` class, so the secondary applies. If this changes in the future, a good tertiary is typically:

- A lighter tint of the primary (Dana-Farber model: `#41B6E6` is a lighter, less saturated version of `#00629B`)
- Or a darker shade of the primary (Limerick model: `#003726` is a darker version of `#005335`)

A tertiary should stay in the same hue family as the primary. Introducing a third unrelated hue creates visual complexity without a payoff.

### Step 6: Sanity checks

Before committing to a palette:

1. **Grayscale test:** convert both colors to grayscale. They should still look clearly different. If they merge, the value gap is too small.
2. **Colorblind test:** confirm the primary and secondary are not both in the red-green axis. A cool primary + amber secondary passes this automatically.
3. **Subtitle readability:** render the secondary as text on a white background at ~14px. If it's hard to read, it is too light — reduce lightness until it passes WCAG AA contrast (4.5:1 ratio against white). Tools like [contrast-ratio.com](https://contrast-ratio.com) or browser DevTools accessibility panels can check this.
4. **Navbar fatigue test:** look at the primary as a full-width navbar background for 30 seconds. If it feels harsh or tiring, the primary is too saturated or too light — reduce saturation or lightness.

---

## Quick reference: palette selection at a glance

```
Institutional brand color
        ↓
Is it cool (90–270° on color wheel)?
  YES → darken to 18–32% lightness, keep hue
  NO  → find a secondary brand color that is cool, or derive one from geography/identity
        ↓
Primary: [cool hue] at 18–32% lightness, 50–90% saturation
        ↓
Secondary: amber (~35–40°)
  Primary lightness < 22% → use #FFA300
  Primary lightness 22–32% → use #F09500 or #E08C00
  Adjust hue ±5° if needed for visual harmony
        ↓
Value gap between primary and secondary: target 35–46 lightness points
        ↓
Run sanity checks: grayscale, colorblind, subtitle readability, navbar fatigue
```
