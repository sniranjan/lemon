// Reel 1: "Age 3 to age 12" — all 13 levels, one second each, with a real page from each.
import React from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { Blob, CREAM, Chip, EndCard, HAND, HEAD, INK, LEVELS, Mascot, Page, SAFE, SUN, usePop } from "./brand";

const PAGES: Record<string, number> = {
  chicks: 2, ducklings: 4, bunnies: 4, kittens: 3, puppies: 4, cubs: 3, foxes: 7,
  owls: 7, otters: 2, pandas: 8, penguins: 7, lions: 9, whales: 7,
};
export const HOOK = 45;
export const STEP = 30;
export const END = 75;
export const LADDER_FRAMES = HOOK + LEVELS.length * STEP + END;

const Hook: React.FC = () => {
  const a = usePop(0);
  const b = usePop(12);
  return (
    <AbsoluteFill style={{ background: SUN, alignItems: "center", justifyContent: "center", paddingBottom: 200 }}>
      <Blob color="#fff" size={620} x={-200} y={-160} opacity={0.3} />
      <div style={{ ...HEAD, fontSize: 130, textAlign: "center", transform: `scale(${a})` }}>From age 3<br />to age 12</div>
      <div style={{ ...HAND, fontSize: 70, color: INK, marginTop: 40, opacity: b }}>in 13 little steps</div>
    </AbsoluteFill>
  );
};

const Step: React.FC<{ i: number }> = ({ i }) => {
  const lv = LEVELS[i];
  const frame = useCurrentFrame();
  const m = usePop(0, 10);
  const pg = usePop(2, 20);
  const tilt = i % 2 ? 4 : -4;
  const shift = interpolate(frame, [0, STEP], [0, -30]);
  return (
    <AbsoluteFill style={{ background: lv.color, overflow: "hidden" }}>
      <Blob color="#fff" size={560} x={i % 2 ? 640 : -180} y={-120} opacity={0.28} />
      <div style={{ position: "absolute", top: SAFE.top, left: SAFE.side, right: SAFE.side, display: "flex", alignItems: "center", gap: 30 }}>
        <div style={{ width: 190, height: 190, borderRadius: "50%", background: "#fff", border: `5px solid ${INK}`, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${m})` }}>
          <Mascot slug={lv.slug} size={150} />
        </div>
        <div>
          <div style={{ ...HEAD, fontSize: 120 }}>{lv.name}</div>
          <div style={{ marginTop: 10 }}><Chip size={46}>Age {lv.age} · {lv.grade} work</Chip></div>
        </div>
      </div>
      <div style={{ position: "absolute", left: 140, top: 480 + (1 - pg) * 900 + shift, transform: `rotate(${tilt}deg)` }}>
        <Page src={`${lv.slug}-${PAGES[lv.slug]}`} width={800} />
      </div>
      <div style={{ position: "absolute", right: 60, top: 60, ...HEAD, fontSize: 40, color: INK, background: CREAM, borderRadius: 999, padding: "8px 24px", border: `4px solid ${INK}` }}>
        {i + 1} / 13
      </div>
    </AbsoluteFill>
  );
};

export const Ladder: React.FC = () => (
  <AbsoluteFill style={{ background: CREAM }}>
    <Sequence durationInFrames={HOOK}><Hook /></Sequence>
    {LEVELS.map((_, i) => (
      <Sequence key={i} from={HOOK + i * STEP} durationInFrames={STEP}><Step i={i} /></Sequence>
    ))}
    <Sequence from={HOOK + LEVELS.length * STEP}>
      <EndCard line={<>Real pages,<br />about two grades ahead</>} sub="free previews · link in bio" />
    </Sequence>
  </AbsoluteFill>
);
