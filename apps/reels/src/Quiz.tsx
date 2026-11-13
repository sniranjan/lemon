// Reel 2: "Can your kid do this?" — zoom into one problem per age, count down 3-2-1, the answer writes in.
import React from "react";
import { AbsoluteFill, Img, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { BY_SLUG, Blob, CORAL, CREAM, Chip, EndCard, HAND, HEAD, INK, Mascot, SAFE, SUN, fade, usePop } from "./brand";

type Round = {
  slug: string; page: number;
  card: { x: number; y: number; w: number; h: number }; // the problem, in pixels of the 1080px-wide page
  answer: string; ax: number; ay: number; size: number; // where the answer writes in (page pixels)
};
// Coordinates measured on the 1080 x 1398 page renders (apps/reels/public/pages).
const ROUNDS: Round[] = [
  { slug: "kittens", page: 8, card: { x: 76, y: 358, w: 452, h: 168 }, answer: "15", ax: 422, ay: 444, size: 66 },
  { slug: "foxes", page: 7, card: { x: 552, y: 582, w: 452, h: 166 }, answer: "14", ax: 892, ay: 666, size: 62 },
  { slug: "pandas", page: 6, card: { x: 76, y: 358, w: 452, h: 220 }, answer: "15/8", ax: 400, ay: 448, size: 50 },
  { slug: "whales", page: 8, card: { x: 76, y: 432, w: 452, h: 204 }, answer: "(x − 3)(x − 4)", ax: 336, ay: 568, size: 50 },
];
export const Q_HOOK = 45;
export const ROUND = 120;
export const Q_END = 80;
export const QUIZ_FRAMES = Q_HOOK + ROUNDS.length * ROUND + Q_END;

const PAGE_W = 1080;
const PAGE_H = 1398;
const WIN = 860; // the square window the page shows in

const Zoom: React.FC<{ r: Round; t: number; reveal: number }> = ({ r, t, reveal }) => {
  const s0 = WIN / PAGE_H;
  const s1 = (WIN - 60) / r.card.w;
  const s = interpolate(t, [0, 1], [s0, s1]);
  const cx = interpolate(t, [0, 1], [PAGE_W / 2, r.card.x + r.card.w / 2]);
  const cy = interpolate(t, [0, 1], [PAGE_H / 2, r.card.y + r.card.h / 2]);
  return (
    <div style={{ width: WIN, height: WIN, overflow: "hidden", position: "relative", background: "#fff", borderRadius: 36, border: `6px solid ${INK}`, boxShadow: `14px 14px 0 ${INK}` }}>
      <div style={{ position: "absolute", left: WIN / 2 - cx * s, top: WIN / 2 - cy * s, width: PAGE_W, height: PAGE_H, transform: `scale(${s})`, transformOrigin: "0 0" }}>
        <Img src={staticFile(`pages/${r.slug}-${r.page}.png`)} style={{ width: PAGE_W, height: PAGE_H, display: "block" }} />
        <div style={{ position: "absolute", left: r.ax, top: r.ay, transform: "translate(-50%, -50%)", ...HAND, fontSize: r.size, color: CORAL, whiteSpace: "nowrap", clipPath: `inset(0 ${(1 - reveal) * 100}% 0 0)` }}>
          {r.answer}
        </div>
      </div>
    </div>
  );
};

const RoundScene: React.FC<{ r: Round; n: number }> = ({ r, n }) => {
  const lv = BY_SLUG[r.slug];
  const frame = useCurrentFrame();
  const head = usePop(0, 11);
  const t = interpolate(frame, [10, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: (x) => 1 - (1 - x) ** 3 });
  const count = frame < 45 ? null : frame < 60 ? 3 : frame < 75 ? 2 : frame < 90 ? 1 : null;
  const reveal = interpolate(frame, [90, 104], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: lv.color, alignItems: "center" }}>
      <Blob color="#fff" size={600} x={n % 2 ? 620 : -220} y={1180} opacity={0.25} />
      <div style={{ marginTop: SAFE.top - 20, display: "flex", alignItems: "center", gap: 26, transform: `scale(${head})` }}>
        <Mascot slug={r.slug} size={150} />
        <div>
          <div style={{ ...HEAD, fontSize: 112 }}>Age {lv.age}</div>
          <Chip size={44}>{lv.grade} work</Chip>
        </div>
      </div>
      <div style={{ marginTop: 50 }}><Zoom r={r} t={t} reveal={reveal} /></div>
      <div style={{ position: "absolute", top: 1390, width: "100%", textAlign: "center", ...HEAD, fontSize: 96 }}>
        {count ? <span style={{ background: CREAM, border: `6px solid ${INK}`, borderRadius: 999, padding: "4px 54px" }}>{count}</span> : null}
        {reveal > 0 ? <span style={{ ...HAND, fontSize: 84, opacity: fade(frame, 96) }}>{lv.name} level ✓</span> : null}
      </div>
    </AbsoluteFill>
  );
};

const Hook: React.FC = () => {
  const a = usePop(0);
  const b = usePop(14);
  return (
    <AbsoluteFill style={{ background: SUN, alignItems: "center", justifyContent: "center", paddingBottom: 200 }}>
      <div style={{ ...HEAD, fontSize: 136, textAlign: "center", transform: `scale(${a})` }}>Can your kid<br />do this?</div>
      <div style={{ ...HAND, fontSize: 68, marginTop: 40, color: INK, opacity: b }}>answer before the timer 👀</div>
    </AbsoluteFill>
  );
};

export const Quiz: React.FC = () => (
  <AbsoluteFill style={{ background: CREAM }}>
    <Sequence durationInFrames={Q_HOOK}><Hook /></Sequence>
    {ROUNDS.map((r, i) => (
      <Sequence key={r.slug} from={Q_HOOK + i * ROUND} durationInFrames={ROUND}><RoundScene r={r} n={i} /></Sequence>
    ))}
    <Sequence from={Q_HOOK + ROUNDS.length * ROUND}>
      <EndCard line="Every level runs about two grades ahead" sub="free previews · link in bio" />
    </Sequence>
  </AbsoluteFill>
);
