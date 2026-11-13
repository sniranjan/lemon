// Reel 3: "A few pages a day" — the page counter runs 1 → 200 while real pages pile up, then the next level.
import React from "react";
import { AbsoluteFill, Easing, Sequence, interpolate, random, useCurrentFrame } from "remotion";
import { CORAL, CREAM, Chip, EndCard, HAND, HEAD, INK, Mascot, Page, SAFE, SUN, TEAL, fade, usePop } from "./brand";

export const S_HOOK = 50;
export const PILE = 210;
export const NEXT = 60;
export const S_END = 80;
export const STACK_FRAMES = S_HOOK + PILE + NEXT + S_END;

const PAGES = [2, 3, 4, 5].map((p) => `chicks-${p}`);
const DROPS = 34; // pages that land (the counter says 200: the pile stands for them)

const Hook: React.FC = () => {
  const a = usePop(0);
  const b = usePop(16);
  return (
    <AbsoluteFill style={{ background: SUN, alignItems: "center", justifyContent: "center", paddingBottom: 200 }}>
      <div style={{ ...HEAD, fontSize: 132, textAlign: "center", transform: `scale(${a})` }}>A few pages<br />a day</div>
      <div style={{ ...HAND, fontSize: 72, marginTop: 40, opacity: b }}>does it add up?</div>
    </AbsoluteFill>
  );
};

const Pile: React.FC = () => {
  const frame = useCurrentFrame();
  const prog = interpolate(frame, [0, PILE - 30], [0, 1], { extrapolateRight: "clamp", easing: Easing.in(Easing.quad) });
  const page = Math.max(1, Math.round(prog * 200));
  const landed = prog * DROPS;
  return (
    <AbsoluteFill style={{ background: CREAM, alignItems: "center" }}>
      <div style={{ marginTop: SAFE.top, ...HEAD, fontSize: 64, color: TEAL }}>Chicks Reading · page</div>
      <div style={{ ...HEAD, fontSize: 210, lineHeight: 1 }}>{page}</div>
      <div style={{ ...HAND, fontSize: 58, color: CORAL, marginTop: 6 }}>{page < 200 ? "a few pages a day, side by side" : "all 200 pages!"}</div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 680, height: 900 }}>
        {Array.from({ length: DROPS }).map((_, i) => {
          const t = Math.min(1, Math.max(0, landed - i));
          if (t <= 0) return null;
          const rot = (random(`r${i}`) - 0.5) * 12;
          const dx = (random(`x${i}`) - 0.5) * 60;
          const y = interpolate(t, [0, 1], [1100, 0], { easing: Easing.out(Easing.cubic) }) - i * 4;
          return (
            <div key={i} style={{ position: "absolute", left: 540 - 260 + dx, top: 120 + y, transform: `rotate(${rot}deg)`, opacity: 1 }}>
              <Page src={PAGES[i % PAGES.length]} width={520} style={{ boxShadow: `6px 6px 0 ${INK}` }} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Next: React.FC = () => {
  const frame = useCurrentFrame();
  const a = usePop(0, 10);
  const b = usePop(22, 10);
  return (
    <AbsoluteFill style={{ background: TEAL, alignItems: "center", justifyContent: "center", paddingBottom: 220 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 40, transform: `scale(${a})` }}>
        <Mascot slug="chicks" size={230} />
        <div style={{ ...HEAD, fontSize: 88 }}>Chicks Reading:<br />done ✓</div>
      </div>
      <div style={{ marginTop: 70, display: "flex", alignItems: "center", gap: 30, transform: `scale(${b})`, opacity: fade(frame, 22) }}>
        <Chip size={52}>Next up</Chip>
        <Mascot slug="ducklings" size={170} />
        <div style={{ ...HEAD, fontSize: 84 }}>Ducklings</div>
      </div>
    </AbsoluteFill>
  );
};

export const Stack: React.FC = () => (
  <AbsoluteFill style={{ background: CREAM }}>
    <Sequence durationInFrames={S_HOOK}><Hook /></Sequence>
    <Sequence from={S_HOOK} durationInFrames={PILE}><Pile /></Sequence>
    <Sequence from={S_HOOK + PILE} durationInFrames={NEXT}><Next /></Sequence>
    <Sequence from={S_HOOK + PILE + NEXT}>
      <EndCard line={<>A few pages a day.<br />13 levels, ages 3 to 12.</>} sub="free previews · link in bio" />
    </Sequence>
  </AbsoluteFill>
);
