import { loadFont } from "@remotion/fonts";
import React from "react";
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import levelsJson from "../public/levels.json";

export const INK = "#1f2a44";
export const CREAM = "#fff8ec";
export const SUN = "#ffc83d";
export const CORAL = "#ff6b5e";
export const TEAL = "#10a99a";
export const SKY = "#4d96ff";

export type Level = { slug: string; name: string; age: number; grade: string; color: string; mascot: string };
export const LEVELS = levelsJson as Level[];
export const BY_SLUG = Object.fromEntries(LEVELS.map((l) => [l.slug, l])) as Record<string, Level>;

loadFont({ family: "Fredoka", url: staticFile("fonts/Fredoka-Bold.woff2"), weight: "700" });
loadFont({ family: "Gochi", url: staticFile("fonts/GochiHand-Regular.woff2") });

export const HEAD: React.CSSProperties = { fontFamily: "Fredoka, 'Arial Rounded MT Bold', Arial, sans-serif", fontWeight: 700, color: INK, lineHeight: 1.05 };

// Fredoka has no superscript digits except ² ³: draw every run of ⁰¹²³⁴⁵⁶⁷⁸⁹⁻ as a raised run in the same font.
const SUP: Record<string, string> = { "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "−" };
export const Rich: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split(/([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)/).map((part, k) =>
      k % 2 ? (
        <span key={k} style={{ fontSize: "0.58em", position: "relative", top: "-0.75em", marginLeft: "0.04em" }}>{[...part].map((c) => SUP[c]).join("")}</span>
      ) : (
        <React.Fragment key={k}>{part}</React.Fragment>
      ),
    )}
  </>
);
export const HAND: React.CSSProperties = { fontFamily: "Gochi" };

// Instagram covers the bottom ~320px (caption, buttons) and the right ~140px of a reel: keep text in the middle.
export const SAFE = { top: 200, bottom: 1500, side: 90 };

export const usePop = (delay = 0, damping = 12) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping } });
};

export const Page: React.FC<{ src: string; width: number; style?: React.CSSProperties }> = ({ src, width, style }) => (
  <Img
    src={staticFile(`pages/${src}.png`)}
    style={{ width, display: "block", borderRadius: 14, border: `4px solid ${INK}`, boxShadow: `12px 12px 0 ${INK}`, ...style }}
  />
);

export const Mascot: React.FC<{ slug: string; size: number; style?: React.CSSProperties }> = ({ slug, size, style }) => (
  <Img src={staticFile(BY_SLUG[slug].mascot)} style={{ width: size, height: size, ...style }} />
);

export const Logo: React.FC<{ width: number }> = ({ width }) => (
  <Img src={staticFile("logo.png")} style={{ width, display: "block" }} />
);

export const Blob: React.FC<{ color: string; size: number; x: number; y: number; opacity?: number }> = ({
  color, size, x, y, opacity = 0.35,
}) => (
  <div style={{ position: "absolute", left: x, top: y, width: size, height: size, borderRadius: "50%", background: color, opacity }} />
);

export const Chip: React.FC<{ children: React.ReactNode; bg?: string; color?: string; size?: number }> = ({
  children, bg = INK, color = "#fff", size = 44,
}) => (
  <div style={{ ...HEAD, display: "inline-block", background: bg, color, fontSize: size, padding: "14px 34px", borderRadius: 999 }}>
    {children}
  </div>
);

export const fade = (frame: number, start: number, len = 8) =>
  interpolate(frame, [start, start + len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

export const EndCard: React.FC<{ line: React.ReactNode; sub?: string }> = ({ line, sub }) => {
  const p = usePop(0);
  const q = usePop(10);
  return (
    <div style={{ position: "absolute", inset: 0, background: CREAM, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: `0 ${SAFE.side}px 260px` }}>
      <Blob color={SUN} size={700} x={-260} y={-200} />
      <Blob color={TEAL} size={520} x={700} y={1350} opacity={0.25} />
      <div style={{ transform: `scale(${p})`, marginBottom: 60 }}><Logo width={760} /></div>
      <div style={{ ...HEAD, fontSize: 84, textAlign: "center", transform: `translateY(${(1 - q) * 40}px)`, opacity: q }}>{line}</div>
      {sub ? <div style={{ ...HAND, fontSize: 60, color: CORAL, marginTop: 34, textAlign: "center", opacity: q }}>{sub}</div> : null}
    </div>
  );
};
