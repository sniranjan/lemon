// "Little hands" reels: calm, not a quiz. What the CDC says most kids do by an age (hand and pencil skills),
// the CDC's own ideas to help, the CDC's "talk with your child's doctor" line, then our closing card.
// Only CDC text (Learn the Signs. Act Early., cdc.gov/act-early/milestones/N-years.html, public domain); wording
// is the CDC's with pronouns made neutral and examples trimmed. Never a test, never a diagnosis.
import React from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { BY_SLUG, CORAL, CREAM, EndCard, HAND, HEAD, INK, Logo, Mascot, SAFE } from "./brand";
import { tint } from "./challenges";

export type MilestoneSpec = { age: number; mascot: string; milestones: string[]; tips: string[] };

const HOOK = 100;
const STEP = 48; // between list items appearing
const HOLD = 110; // after the last item
const CARE = 150;
const CLOSE = 120;
const listFrames = (n: number) => 20 + n * STEP + HOLD;
export const milestoneFrames = (s: MilestoneSpec) => HOOK + listFrames(s.milestones.length) + listFrames(s.tips.length) + CARE + CLOSE;

const SOURCE = "Source: CDC · Learn the Signs. Act Early.";

const appear = (frame: number, at: number) => interpolate(frame, [at, at + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

const Source: React.FC = () => (
  <div style={{ position: "absolute", top: 1400, left: 0, right: 0, textAlign: "center", ...HEAD, fontSize: 38, color: INK, opacity: 0.75 }}>{SOURCE}</div>
);

const Top: React.FC = () => (
  <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", justifyContent: "center" }}><Logo width={440} /></div>
);

const Hook: React.FC<{ s: MilestoneSpec; bg: string }> = ({ s, bg }) => {
  const frame = useCurrentFrame();
  const a = appear(frame, 0) * 0.3 + 0.7;
  return (
    <AbsoluteFill style={{ background: bg, alignItems: "center", justifyContent: "center", paddingBottom: 240 }}>
      <Top />
      <div style={{ width: 280, height: 280, borderRadius: 140, background: "#fff", border: `7px solid ${INK}`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 50, transform: `scale(${a})` }}>
        <Mascot slug={s.mascot} size={210} />
      </div>
      <div style={{ ...HEAD, fontSize: 70, background: INK, color: "#fff", borderRadius: 999, padding: "12px 48px", marginBottom: 40 }}>Little hands</div>
      <div style={{ ...HEAD, fontSize: 120, textAlign: "center", transform: `scale(${a})` }}>Hand skills<br />at age {s.age}</div>
      <div style={{ ...HAND, fontSize: 62, marginTop: 44, textAlign: "center", padding: `0 ${SAFE.side}px` }}>what most kids can do,<br />and easy ways to help 🖍️</div>
      <Source />
    </AbsoluteFill>
  );
};

const List: React.FC<{ bg: string; title: string; items: string[]; mark: string }> = ({ bg, title, items, mark }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: bg }}>
      <Top />
      <div style={{ position: "absolute", top: 260, height: 1100, left: SAFE.side, right: SAFE.side, display: "flex", flexDirection: "column", justifyContent: "center", gap: 30 }}>
        <div style={{ ...HEAD, fontSize: 74, textAlign: "center", marginBottom: 10, opacity: appear(frame, 0) }}>{title}</div>
        {items.map((t, k) => {
          const o = appear(frame, 20 + k * STEP);
          return (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: 26, background: "#fff", border: `5px solid ${INK}`, borderRadius: 32, padding: "24px 30px", opacity: o, transform: `translateY(${(1 - o) * 30}px)`, boxShadow: `8px 8px 0 ${INK}` }}>
              <div style={{ fontSize: 62, flexShrink: 0 }}>{mark}</div>
              <div style={{ ...HEAD, fontSize: 50, lineHeight: 1.15 }}>{t}</div>
            </div>
          );
        })}
      </div>
      <Source />
    </AbsoluteFill>
  );
};

const Care: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: CREAM, alignItems: "center", justifyContent: "center", paddingBottom: 260, padding: `0 ${SAFE.side + 20}px 260px` }}>
      <div style={{ ...HEAD, fontSize: 96, textAlign: "center", opacity: appear(frame, 0) }}>You know your<br />child best 💛</div>
      <div style={{ ...HEAD, fontSize: 60, textAlign: "center", marginTop: 50, opacity: appear(frame, 25) }}>Have a concern? Talk with your child's doctor and ask about developmental screening.</div>
      <div style={{ ...HEAD, fontSize: 50, color: CORAL, marginTop: 50, textAlign: "center", opacity: appear(frame, 45) }}>Source: CDC · cdc.gov/ActEarly</div>
    </AbsoluteFill>
  );
};

export const Milestones: React.FC<{ spec: MilestoneSpec }> = ({ spec }) => {
  const bg = tint(BY_SLUG[spec.mascot].color, 0.7);
  const m = listFrames(spec.milestones.length);
  const t = listFrames(spec.tips.length);
  return (
    <AbsoluteFill style={{ background: bg }}>
      <Sequence durationInFrames={HOOK}><Hook s={spec} bg={bg} /></Sequence>
      <Sequence from={HOOK} durationInFrames={m}><List bg={bg} title={`Most kids (75%+) by age ${spec.age}`} items={spec.milestones} mark="✅" /></Sequence>
      <Sequence from={HOOK + m} durationInFrames={t}><List bg={bg} title="Easy ways to help" items={spec.tips} mark="💡" /></Sequence>
      <Sequence from={HOOK + m + t} durationInFrames={CARE}><Care /></Sequence>
      <Sequence from={HOOK + m + t + CARE}><EndCard line={"Every kid grows\nat their own pace"} sub={"printable worksheets, ages 3–12\npaperlessons.com"} /></Sequence>
    </AbsoluteFill>
  );
};

// CDC milestone pages (Movement/Physical + the pencil and letter items under Cognitive) and their own tips.
export const MILESTONES: MilestoneSpec[] = [
  { age: 3, mascot: "chicks",
    milestones: ["Strings items together, like large beads or macaroni", "Draws a circle, when you show them how", "Puts on some clothes by themselves, like loose pants or a jacket", "Uses a fork"],
    tips: ["Play with playdough: squish, press, pinch and roll balls. It builds hand and finger muscles for writing, buttoning and cutting.", "Keep an activity box with paper, crayons and coloring books. Draw lines and shapes together.", "Let them help make meals, like washing fruit or stirring."] },
  { age: 4, mascot: "bunnies",
    milestones: ["Holds a crayon or pencil between fingers and thumb (not a fist)", "Draws a person with three or more body parts", "Unbuttons some buttons", "Serves themselves food or pours water, with adult supervision"],
    tips: ["Give toys that spark imagination: dress-up clothes, pots and pans, or blocks to build with.", "Play simple games, such as Tic-Tac-Toe or matching games.", "Let them help with simple chores, like wiping down tables."] },
  { age: 5, mascot: "cubs",
    milestones: ["Buttons some buttons", "Writes some letters in their name", "Names some letters when you point to them", "Counts to 10"],
    tips: ["Let them do things themselves, like buttoning a shirt or pouring water, even if it's not perfect. Try not to fix it.", "Keep crayons, paper, paint, child scissors and glue for creative play.", "Play with puzzles and building blocks."] },
];
