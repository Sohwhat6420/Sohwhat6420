"""Build only the LinkedIn contact card: python tools/linkedin_card.py.

Uses the same glass, theme tokens and outlined Hanken Grotesk as the about
tiles. Separate mobile artwork keeps the original words readable on a phone.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "koi"))
from koilib import Doc, GLASS_PAD, THEMES, glass  # noqa: E402


def card(theme, mobile=False):
    width, height = (388 if mobile else 798), 62
    doc = Doc(width, height, "Find me on LinkedIn.", "Find me on LinkedIn.")
    doc.pad = GLASS_PAD
    doc.body.append(glass(doc, theme, 0, 0, width, height, 18))
    gold = theme["gold"]
    # A quiet contact glyph and outward arrow use the existing gold accent.
    doc.body.append(
        '<circle cx="33" cy="31" r="18" fill="%s" fill-opacity=".08" '
        'stroke="%s" stroke-opacity=".4"/>' % (gold, gold)
    )
    doc.body.append(
        '<g fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round">'
        '<circle cx="33" cy="27" r="4"/>'
        '<path d="M25 39c0-8 16-8 16 0"/></g>' % gold
    )
    x = 66 if mobile else 74
    prefix, advance = doc.text("Find me on ", x, 38, "sans", 21, theme["dim"])
    label, _ = doc.text("LinkedIn.", x + advance, 38, "sansm", 21, gold)
    doc.body.extend((prefix, label))
    doc.body.append(
        '<path d="M%d 37l12-12m-10 0h10v10" fill="none" stroke="%s" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        % (width - 40, gold)
    )
    return doc


if __name__ == "__main__":
    for name, theme in THEMES.items():
        for mobile in (False, True):
            suffix = "-m" if mobile else ""
            target = HERE.parent / "assets" / ("contact-linkedin%s-%s.svg" % (suffix, name))
            target.write_text(card(theme, mobile).render(), encoding="utf-8", newline="\n")
            print(target.name)
