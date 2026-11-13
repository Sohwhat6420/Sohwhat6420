# "Download CV (PDF)" button: proposal

Nothing here is live. `README.md` and `assets/` are untouched on this branch; this folder only holds the options.

- **Compare:** `comparison.png` (current against A, B and C; light and dark; desktop and phone).
- **Variants:** `assets/cv-download-{a,b,c}-{light,dark}.svg`, drawn by `make_variants.py`.

## What was wrong (measured, desktop profile view)

| | Current | A, B, C |
| --- | --- | --- |
| Second line of the button | Live text in the visitor's own font. It touches the border with Windows fonts, crosses it with Android fonts, and is cut off with wider fonts. | Outlined Instrument Sans, like the cards. Same width everywhere, 25 px clear of the edge. |
| Space inside | 26 px before the arrow, about 7 px after the text (Windows fonts). | 22 px before the arrow, 25 px after the text. |
| Gap above (paragraph to button) | 18 px | 18 px |
| Gap below (button to caption) | 30.6 px | 14.6 px |
| Caption to the next heading | 26.9 px | 26.9 px |
| Left edge | Flush with the text column (0 px). | The same. |

The left edge was already right: the button belongs to the paragraph and caption, which sit at 0 px. The cards sit about 15 px further in because of the shadow room inside their own images, so the button should not follow them. What made it look off was the caption floating further from the button (30.6 px) than the button is from the paragraph above (18 px), and the text pressed against the right-hand curve.

## Recommendation: B (A is the close second)

A and B are the same button: gold 1 px ring, same two lines, same size. B adds the cards' glass as a fill.

- **Why B:** a visitor whose GitHub theme and system theme disagree is served the wrong theme's image. The live button and A then lose their title (dark letters on the dark page, or light on white); B and C keep it, because they carry their own background. I rendered that case to check. B also reads more like a surface you can press, in the same material as the cards.
- **Why you might prefer A:** on matched themes it is the cleanest of the three, and the independent reviewer picked it on looks alone, finding B's fill nearly invisible on white and a little grey on dark.
- **C** is the strongest call to action and fully readable in the mismatch case, but it is the loudest thing between the banner and section 01.

Also changed in all three: the arrow nudges three times after the page loads and then rests (the live one loops for ever), and the tray under the arrow stays still.

## To apply a variant (B shown)

1. Copy `proposals/cv-button/assets/cv-download-b-light.svg` and `-dark.svg` over `assets/cv-download-light.svg` and `-dark.svg`.
2. In `README.md`, on the button's line change `width="318"` to `width="327"`, add `<br>` after its closing `</a>`, and delete the blank line between it and the `<sub>Short on time? …</sub>` line, so the caption joins the button's paragraph. No wording, link or alt text changes.
3. Delete `proposals/`.

## How it was checked

Headless bundled Chromium, GitHub's own markdown parser (cmark-gfm) and stylesheet, 14 px profile text, 846 px column at desktop width; phones at 412 px and 360 px. Fonts were stand-ins with matching widths (Selawik for Segoe UI, Roboto for Android).

Not confirmed: the live profile page could not be opened from this session, so the phone column width (330 px on a 412 px screen) is worked out from GitHub's padding, and Apple devices were not rendered (the "cut off" result there is inferred from Inter, which is close to Apple's font in width).
