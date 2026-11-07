// The gift card as a real PDF: one US Letter page that looks like the on-screen card (src/components/GiftCard.tsx).
//
// The fixed parts (logo, paper circles, "a gift for", the dashed code box and its labels, the mascots) are a
// background PDF drawn once with Chromium (scripts/gift-card/render_background.py) and bundled as base64
// (worker/giftCardAssets.ts, with the site's fonts: Fredoka, Nunito, Gochi Hand; SIL OFL). Here pdf-lib draws
// this gift's own words on top: who it's for, who it's from, the message (or our little note), the gift line and
// the code. Every box is measured with the real font, so long names and a 300-character message shrink and wrap
// instead of overflowing. The output is deterministic: same gift, same bytes.
//
// Positions are CSS px on an 816 x 1056 page (as in the background), converted to PDF points (x 0.75, y flipped).
import fontkit from "@pdf-lib/fontkit";
import {
  PDFDocument,
  concatTransformationMatrix,
  popGraphicsState,
  pushGraphicsState,
  rgb,
  setCharacterSpacing,
  type PDFFont,
  type PDFPage,
  type RGB,
} from "pdf-lib";
import { dollars } from "../src/lib/giftShare";
import { BACKGROUND, FREDOKA_BOLD, GOCHI_HAND, NUNITO_BOLD, NUNITO_REGULAR } from "./giftCardAssets";

export type CardGift = {
  kind: "all" | "credit";
  amountCents: number;
  code: string;
  childName: string | null;
  buyerName: string | null;
  message: string | null;
};

const PX = 0.75; // CSS px → PDF pt
const PAGE_H = 1056;

/** The boxes this file fills, in CSS px (the background leaves them empty; keep in step with render_background.py). */
export const LAYOUT = {
  left: 57,
  width: 702,
  nameTop: 214, // just under "a gift for"
  topLimit: 610, // the name, "from" and the message all end above this
  whatTop: 630, // "Every level, ages 3 to 12" / "$50 to spend on any level"
  detailTop: 668,
  detailWidth: 562,
  codeBox: { top: 734, bottom: 914 }, // dashed box in the background
  codeTop: 777,
  messageWidth: 618, // the message card: 88% of the column
};

const INK = rgb(0x1f / 255, 0x2a / 255, 0x44 / 255);
const CORAL = rgb(1, 0x6b / 255, 0x5e / 255);
const CREAM = rgb(1, 0xf8 / 255, 0xec / 255);
/** ink at `a` opacity on white */
const inkOn = (a: number) => rgb(1 - a * (1 - 0x1f / 255), 1 - a * (1 - 0x2a / 255), 1 - a * (1 - 0x44 / 255));

export const NOTE = "little lessons, one page at a time: to read, count and grow with, a few pages a day.";
const DETAIL = {
  all: "All 13 levels of printable reading and math pages, from first words and counting to fractions and algebra.",
  credit: "Printable reading and math pages for ages 3 to 12, from first words and counting to fractions and algebra.",
};

// ---------------------------------------------------------------------------------------------------------
// Fonts and text fitting

export type CardFonts = { display: PDFFont; body: PDFFont; bold: PDFFont; hand: PDFFont };

/** Keep only characters the font can draw (emoji, scripts we don't carry): never a blank box or a crash. */
export function drawable(text: string, font: PDFFont): string {
  let has = charSets.get(font.name);
  if (!has) charSets.set(font.name, (has = new Set(font.getCharacterSet())));
  return [...text].filter((ch) => ch === "\n" || has.has(ch.codePointAt(0)!)).join("");
}
// Per font (by its PostScript name: the four bundled fonts never change), kept across cards.
const charSets = new Map<string, Set<number>>();

/**
 * Width of `text` at `size`: the sum of each character's advance, measured once per character. pdf-lib draws
 * glyphs at their advance widths (no kerning), so this is what ends up on the page, and it keeps fitting text
 * cheap (font.widthOfTextAtSize runs a full shaping pass on every call).
 */
function widthOf(font: PDFFont, text: string, size: number): number {
  let cache = advances.get(font.name);
  if (!cache) advances.set(font.name, (cache = new Map()));
  let units = 0;
  for (const ch of text) {
    let a = cache.get(ch);
    if (a === undefined) cache.set(ch, (a = font.widthOfTextAtSize(ch, 1000)));
    units += a;
  }
  return (units * size) / 1000;
}
const advances = new Map<string, Map<string, number>>();

const oneLine = (s: string) => s.replace(/\s+/g, " ").trim();

/** Break one paragraph into lines no wider than `max` (words first; a word too long on its own is cut). */
function wrap(text: string, font: PDFFont, size: number, max: number): string[] {
  const w = (s: string) => widthOf(font, s, size);
  const lines: string[] = [];
  let cur = "";
  for (const word of text.split(" ").filter(Boolean)) {
    const next = cur ? `${cur} ${word}` : word;
    if (w(next) <= max) {
      cur = next;
      continue;
    }
    if (cur) lines.push(cur);
    cur = "";
    let rest = word;
    while (w(rest) > max) {
      const chars = [...rest];
      let n = chars.length - 1;
      while (n > 1 && w(chars.slice(0, n).join("")) > max) n--;
      lines.push(chars.slice(0, n).join(""));
      rest = chars.slice(n).join("");
    }
    cur = rest;
  }
  if (cur) lines.push(cur);
  return lines;
}

/** Paragraphs (line breaks kept, blank lines too) → lines. */
const wrapAll = (text: string, font: PDFFont, size: number, max: number) =>
  text.split("\n").flatMap((p) => (oneLine(p) ? wrap(oneLine(p), font, size, max) : [""]));

/** Cut to `n` lines, ending the last with "…" so it still fits. */
function clip(lines: string[], n: number, font: PDFFont, size: number, max: number): string[] {
  if (lines.length <= n) return lines;
  const out = lines.slice(0, n);
  let last = out[n - 1].trimEnd();
  while (last && widthOf(font, `${last}…`, size) > max) last = [...last].slice(0, -1).join("").trimEnd();
  out[n - 1] = `${last}…`;
  return out;
}

/**
 * The biggest size from `sizes` at which `text` wraps into at most `maxLines(size)` lines; at the smallest size
 * whatever doesn't fit is cut with "…".
 */
function fit(text: string, font: PDFFont, max: number, sizes: number[], maxLines: (size: number) => number) {
  for (const size of sizes) {
    const lines = wrapAll(text, font, size, max);
    if (lines.length <= maxLines(size)) return { size, lines };
  }
  const size = sizes.at(-1)!;
  return { size, lines: clip(wrapAll(text, font, size, max), Math.max(1, maxLines(size)), font, size, max) };
}

/** One line at the biggest size from `sizes` that fits; at the smallest, letters are cut from the end ("…"). */
function shrinkLine(text: string, font: PDFFont, max: number, sizes: number[]) {
  for (const size of sizes) if (widthOf(font, text, size) <= max) return { size, text };
  const size = sizes.at(-1)!;
  let chars = [...text];
  while (chars.length > 1 && widthOf(font, `${chars.join("").trimEnd()}…`, size) > max) chars = chars.slice(0, -1);
  return { size, text: `${chars.join("").trimEnd()}…` };
}

// ---------------------------------------------------------------------------------------------------------
// Layout (pure: measured with the real fonts, nothing drawn yet)

export type TextLine = { text: string; font: keyof CardFonts; size: number; color: RGB; x: number; top: number; lineHeight: number; width: number; spacing?: number; /** drawn with the tilted box */ inBox?: boolean };
export type Card = {
  lines: TextLine[];
  /** the message card (rounded, cream, rotated 1° like the screen card) or the note, both rotated as a group */
  box: { x: number; top: number; width: number; height: number; filled: boolean } | null;
  /** where the top part ends (name, from, message), for the tests */
  topEnd: number;
};

const range = (from: number, to: number, step: number) => {
  const out: number[] = [];
  for (let s = from; s >= to - 1e-9; s -= step) out.push(Math.round(s * 10) / 10);
  return out;
};

export function layoutCard(g: CardGift, fonts: CardFonts): Card {
  const L = LAYOUT;
  const lines: TextLine[] = [];
  const add = (font: keyof CardFonts, size: number, lh: number, color: RGB, x: number, top: number, texts: string[], extra: Partial<TextLine> = {}) => {
    texts.forEach((text, i) =>
      lines.push({ text, font, size, color, x, top: top + i * size * lh, lineHeight: size * lh, width: widthOf(fonts[font], text, size), ...extra }),
    );
    return top + texts.length * size * lh;
  };

  // "a gift for" {child or you}: one line as big as fits, two lines for very long names.
  const child = oneLine(drawable(g.childName ?? "", fonts.display));
  const forName = child || "you";
  const NAME_LH = 1.08;
  const one = range(57.6, 34, 1.6).map((s) => ({ s, n: 1 }));
  const two = range(34, 22, 2).map((s) => ({ s, n: 2 }));
  let name = { size: 22, lines: [forName] };
  for (const { s, n } of [...one, ...two]) {
    const ls = wrap(forName, fonts.display, s, L.width);
    if (ls.length <= n) {
      name = { size: s, lines: ls };
      break;
    }
    name = { size: s, lines: clip(ls, n, fonts.display, s, L.width) };
  }
  let y = add("display", name.size, NAME_LH, INK, L.left, L.nameTop, name.lines);

  // "from {name}", only if given.
  const buyer = oneLine(drawable(g.buyerName ?? "", fonts.bold));
  if (buyer) {
    // One line ("from" never alone on a line): shrink, then cut with "…" for an extreme name.
    const from = shrinkLine(`from ${buyer}`, fonts.bold, L.width, range(23.2, 12.8, 1.6));
    y = add("bold", from.size, 1.3, INK, L.left, y + 10, [from.text]);
  }

  // The message on a cream card, or our own little note so the card never looks empty.
  const message = drawable(g.message ?? "", fonts.body).trim();
  let box: Card["box"] = null;
  if (message) {
    const top = y + 26;
    const PAD_X = 24;
    const PAD_Y = 16;
    const inner = L.messageWidth - 2 * PAD_X;
    const room = L.topLimit - top - 2 * PAD_Y - 6;
    const lh = (s: number) => (s >= 19 ? 1.6 : 1.45);
    const m = fit(message, fonts.body, inner, [20.8, 19.2, 18, 16.8, 15.6, 14.4, 13.2, 12, 11], (s) => Math.floor(room / (s * lh(s))));
    const textTop = top + 3 + PAD_Y;
    const end = add("body", m.size, lh(m.size), INK, L.left + 3 + PAD_X, textTop, m.lines, { inBox: true });
    box = { x: L.left, top, width: L.messageWidth, height: end - top + PAD_Y + 3, filled: true };
  } else {
    const top = y + 30;
    const max = L.detailWidth;
    const n = fit(NOTE, fonts.hand, max, [33.6, 30, 27, 24, 21, 18], (s) => Math.floor((L.topLimit - top) / (s * 1.25)));
    const end = add("hand", n.size, 1.25, inkOn(0.8), L.left, top, n.lines, { inBox: true });
    box = { x: L.left, top, width: max, height: end - top, filled: false };
  }
  const topEnd = box.top + box.height;

  // The gift line and the code (fixed places at the bottom, above and in the dashed box).
  const what = g.kind === "all" ? "Every level, ages 3 to 12" : `${dollars(g.amountCents)} to spend on any level`;
  add("bold", 25.6, 1.25, INK, L.left, L.whatTop, [what]);
  add("bold", 16.8, 1.45, inkOn(0.75), L.left, L.detailTop, clip(wrap(DETAIL[g.kind], fonts.bold, 16.8, L.detailWidth), 2, fonts.bold, 16.8, L.detailWidth));
  const codeSize = 43.2;
  const spacing = codeSize * 0.14;
  add("display", codeSize, 1, INK, L.left + 3 + 24, L.codeTop, [g.code], { spacing });
  const last = lines.at(-1)!;
  last.width += spacing * ([...g.code].length - 1);

  return { lines, box, topEnd };
}

// ---------------------------------------------------------------------------------------------------------
// Drawing

const b64 = (s: string) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
let assets: { background: Uint8Array; fonts: Record<keyof CardFonts, Uint8Array> } | null = null;
/** Decoded on first use, not at Worker start-up. */
function loadAssets() {
  assets ??= {
    background: b64(BACKGROUND),
    fonts: { display: b64(FREDOKA_BOLD), body: b64(NUNITO_REGULAR), bold: b64(NUNITO_BOLD), hand: b64(GOCHI_HAND) },
  };
  return assets;
}

/** The background page with the four fonts embedded (subset to the characters used). */
export async function cardDocument() {
  const a = loadAssets();
  const doc = await PDFDocument.load(a.background, { updateMetadata: false });
  doc.registerFontkit(fontkit);
  // No ligatures, so every letter of a name is its own glyph (and copies out of the PDF as typed).
  const features = { liga: false, clig: false, calt: false, dlig: false };
  const embed = (bytes: Uint8Array) => doc.embedFont(bytes, { subset: true, features });
  const [display, body, bold, hand] = await Promise.all([embed(a.fonts.display), embed(a.fonts.body), embed(a.fonts.bold), embed(a.fonts.hand)]);
  return { doc, fonts: { display, body, bold, hand } satisfies CardFonts };
}

const pt = (px: number) => px * PX;
/** Baseline (in PDF points from the bottom) for a line box starting at `top` px. */
function baseline(font: PDFFont, size: number, top: number, lineHeight: number) {
  const full = font.heightAtSize(size); // ascender to descender
  const ascent = font.heightAtSize(size, { descender: false });
  return pt(PAGE_H - (top + (lineHeight - full) / 2 + ascent));
}

/** Rotate everything drawn in `draw` by `deg` (counterclockwise, like CSS rotate(-deg)) around (cx, cy) in pt. */
function rotated(page: PDFPage, deg: number, cx: number, cy: number, draw: () => void) {
  const r = (deg * Math.PI) / 180;
  const [c, s] = [Math.cos(r), Math.sin(r)];
  page.pushOperators(pushGraphicsState(), concatTransformationMatrix(c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy));
  draw();
  page.pushOperators(popGraphicsState());
}

const roundedRect = (w: number, h: number, r: number) =>
  `M ${r} 0 H ${w - r} A ${r} ${r} 0 0 1 ${w} ${r} V ${h - r} A ${r} ${r} 0 0 1 ${w - r} ${h} H ${r} A ${r} ${r} 0 0 1 0 ${h - r} V ${r} A ${r} ${r} 0 0 1 ${r} 0 Z`;

const FIXED_DATE = new Date("2026-01-01T00:00:00Z");

/** The gift card PDF for one gift. Same gift in, same bytes out. */
export async function giftCardPdf(g: CardGift): Promise<Uint8Array> {
  const { doc, fonts } = await cardDocument();
  const page = doc.getPage(0);
  const card = layoutCard(g, fonts);

  const drawLine = (l: TextLine) => {
    const font = fonts[l.font];
    if (l.spacing) page.pushOperators(setCharacterSpacing(pt(l.spacing)));
    page.drawText(l.text, { x: pt(l.x), y: baseline(font, l.size, l.top, l.lineHeight), size: pt(l.size), font, color: l.color });
    if (l.spacing) page.pushOperators(setCharacterSpacing(0));
  };
  const inBox = (l: TextLine) => Boolean(l.inBox);

  for (const l of card.lines.filter((l) => !inBox(l))) drawLine(l);
  if (card.box) {
    const b = card.box;
    rotated(page, 1, pt(b.x + b.width / 2), pt(PAGE_H - b.top - b.height / 2), () => {
      if (b.filled) {
        page.drawSvgPath(roundedRect(pt(b.width - 3), pt(b.height - 3), pt(16)), {
          x: pt(b.x + 1.5),
          y: pt(PAGE_H - b.top - 1.5),
          color: CREAM,
          borderColor: INK,
          borderWidth: pt(3),
        });
      }
      for (const l of card.lines.filter(inBox)) drawLine(l);
    });
  }

  doc.setTitle(`Paper Lessons gift card ${g.code}`);
  doc.setAuthor("Paper Lessons");
  doc.setSubject("A gift card for printable reading and math pages. Open it at paperlessons.com/redeem.");
  doc.setCreator("paperlessons.com");
  doc.setProducer("paperlessons.com");
  doc.setLanguage("en-US");
  doc.setCreationDate(FIXED_DATE);
  doc.setModificationDate(FIXED_DATE);
  return doc.save();
}
