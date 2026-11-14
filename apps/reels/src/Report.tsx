// "Only 19% of 4th graders got this right" reels: one real released NAEP (Nation's Report Card) question each.
// Question, timer, then the answer with what share of US students picked each choice, one line on the common
// mistake, and our closing card. Questions, choices and percentages are verbatim from the NAEP Questions Tool
// (nationsreportcard.gov/nqt, national results; public domain per its FAQ); the "why" lines are ours.
import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Music, TimerSounds } from "./audio";
import { Timer } from "./Challenge";
import { CORAL, CREAM, EndCard, HAND, HEAD, INK, Logo, Rich, SAFE } from "./brand";

export type ReportSpec = {
  id: string;
  grade: 4 | 8 | 12;
  year: number;
  naepId: string; // e.g. "1992-4M5 #17" (NQT question ID)
  question: string;
  choices: string[];
  correct: number;
  picked: number[]; // percent of students choosing each choice, same order as choices
  why: string; // our one-line explanation of the answer and the common mistake
  seconds: number;
};

const HOOK = 80;
const INTRO = 10;
const REVEAL = 75;
const WHY = 120;
const CLOSE = 120;
export const reportFrames = (s: ReportSpec) => HOOK + INTRO + s.seconds * 30 + REVEAL + WHY + CLOSE;

const GREEN = "#2fa35a";
const BG: Record<number, string> = { 4: "#cfe6ff", 8: "#fff0c2", 12: "#c9eee8" };
const ordinal = (g: number) => `${g}th`;
const LETTERS = "ABCDE";

const Source: React.FC<{ s: ReportSpec }> = ({ s }) => (
  <div style={{ position: "absolute", top: 1450, left: 0, right: 0, textAlign: "center", ...HEAD, fontSize: 32, opacity: 0.7 }}>
    Source: NAEP, the Nation's Report Card · {s.year} · grade {s.grade}
  </div>
);

const Hook: React.FC<{ s: ReportSpec }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = 0.7 + 0.3 * spring({ frame, fps, config: { damping: 11 } });
  const pct = s.picked[s.correct];
  return (
    <AbsoluteFill style={{ background: BG[s.grade], alignItems: "center", justifyContent: "center", paddingBottom: 220 }}>
      <div style={{ position: "absolute", top: 80 }}><Logo width={480} /></div>
      <div style={{ ...HEAD, fontSize: 60, background: INK, color: "#fff", borderRadius: 999, padding: "12px 44px", marginBottom: 40 }}>Nation's Report Card</div>
      <div style={{ ...HEAD, fontSize: 116, textAlign: "center", transform: `scale(${a})`, padding: `0 ${SAFE.side}px` }}>
        Only <span style={{ color: CORAL }}>{pct}%</span> of<br />{ordinal(s.grade)} graders<br />got this right
      </div>
      <div style={{ ...HAND, fontSize: 62, marginTop: 44, textAlign: "center" }}>a real US test question ({s.year})<br />can you? 👀</div>
    </AbsoluteFill>
  );
};

const Question: React.FC<{ s: ReportSpec }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = s.seconds * 30;
  const reveal = spring({ frame: frame - INTRO - total, fps, config: { damping: 14 } });
  const shown = frame >= INTRO + total;
  const why = interpolate(frame, [INTRO + total + REVEAL, INTRO + total + REVEAL + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const long = s.question.length > 110;
  return (
    <AbsoluteFill style={{ background: BG[s.grade] }}>
      <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", justifyContent: "center" }}><Logo width={420} /></div>
      <div style={{ position: "absolute", top: 230, height: 1100, left: SAFE.side, right: SAFE.side, display: "flex", flexDirection: "column", justifyContent: "center", gap: 22 }}>
        <div style={{ ...HEAD, fontSize: long ? 54 : 62, lineHeight: 1.18, marginBottom: 14 }}><Rich text={s.question} /></div>
        {s.choices.map((c, k) => {
          const right = k === s.correct;
          const dim = shown && !right;
          return (
            <div key={k} style={{ position: "relative", display: "flex", alignItems: "center", gap: 22, background: "#fff", border: `5px solid ${shown && right ? GREEN : INK}`, borderRadius: 26, padding: "14px 26px", overflow: "hidden", opacity: dim ? 0.75 : 1 }}>
              {shown ? <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${s.picked[k] * reveal}%`, background: right ? "rgba(47,163,90,.28)" : "rgba(31,42,68,.12)" }} /> : null}
              <div style={{ ...HEAD, fontSize: 50, color: CORAL, position: "relative", width: 44 }}>{LETTERS[k]}</div>
              <div style={{ ...HEAD, fontSize: 52, position: "relative", flex: 1 }}><Rich text={c} /></div>
              {shown ? <div style={{ ...HEAD, fontSize: 48, position: "relative", color: right ? GREEN : INK }}>{right ? "✓ " : ""}{Math.round(s.picked[k] * reveal)}%</div> : null}
            </div>
          );
        })}
        {shown ? (
          <div style={{ ...HEAD, fontSize: 44, textAlign: "center", marginTop: 8, opacity: reveal }}>% of US {ordinal(s.grade)} graders who picked each answer</div>
        ) : null}
      </div>
      {!shown ? <Timer frame={Math.max(0, frame - INTRO)} total={total} /> : null}
      {why > 0 ? (
        <AbsoluteFill style={{ background: CREAM, alignItems: "center", justifyContent: "center", padding: `0 ${SAFE.side + 10}px 240px`, opacity: why }}>
          <div style={{ ...HEAD, fontSize: 70, color: GREEN, marginBottom: 30 }}>Answer: {LETTERS[s.correct]}</div>
          <div style={{ ...HEAD, fontSize: 64, textAlign: "center", lineHeight: 1.2 }}><Rich text={s.why} /></div>
          <div style={{ ...HAND, fontSize: 60, color: CORAL, marginTop: 50 }}>Did you get it? 👇</div>
        </AbsoluteFill>
      ) : null}
      <Source s={s} />
    </AbsoluteFill>
  );
};

export const Report: React.FC<{ spec: ReportSpec }> = ({ spec }) => {
  const q = reportFrames(spec) - HOOK - CLOSE;
  return (
    <AbsoluteFill style={{ background: CREAM }}>
      <Music track="thinking-music" frames={reportFrames(spec)} />
      <Sequence durationInFrames={HOOK}><Hook s={spec} /></Sequence>
      <Sequence from={HOOK} durationInFrames={q}>
        <Question s={spec} />
        <TimerSounds start={INTRO} seconds={spec.seconds} />
      </Sequence>
      <Sequence from={HOOK + q}><EndCard line={"Every kid learns\nat their own pace"} sub={"printable worksheets, ages 3–12\npaperlessons.com"} /></Sequence>
    </AbsoluteFill>
  );
};

const r = (s: Omit<ReportSpec, "id" | "seconds"> & { seconds?: number }): ReportSpec => ({
  ...s,
  seconds: s.seconds ?? 10,
  id: `Report-g${s.grade}-${s.naepId.replace(/[^A-Za-z0-9]+/g, "-").replace(/-$/, "")}`,
});

export const REPORTS: ReportSpec[] = [
  r({ grade: 4, year: 1992, naepId: "1992-4M5 #17", question: "A rectangular carpet is 9 feet long and 6 feet wide. What is the area of the carpet in square feet?",
    choices: ["15", "27", "30", "54"], correct: 3, picked: [45, 16, 19, 19], why: "Area = long × wide: 9 × 6 = 54.\n45% picked 15. They added the sides." }),
  r({ grade: 4, year: 1992, naepId: "1992-4M5 #12", question: "By how much would 217 be increased if the digit 1 were replaced by a digit 5?",
    choices: ["4", "40", "44", "400"], correct: 1, picked: [22, 36, 22, 14], why: "217 becomes 257.\nThe 1 is in the tens place, so it grows by 40." }),
  r({ grade: 4, year: 2013, naepId: "2013-4M6 #12", question: "Which expression has the least value?",
    choices: ["2 + 7 + 0 + 4", "(2 × 7) + 0 + 4", "2 + (7 × 0) + 4", "2 × 7 × 0 × 4"], correct: 3, picked: [19, 9, 35, 36], why: "Anything times 0 is 0.\nSo 2 × 7 × 0 × 4 = 0, the least." }),
  r({ grade: 4, year: 2024, naepId: "2024-4M7 #5", question: "Maya measured the height of the door to her classroom. Which measurement could be the height of the door?",
    choices: ["0.5 mile", "2 yards", "3 feet", "20 inches"], correct: 1, picked: [6, 35, 35, 22], why: "A door is about 6 to 7 feet tall.\nThat's about 2 yards. 3 feet is only waist high!" }),
  r({ grade: 8, year: 1990, naepId: "1990-8M9 #18", question: "If the price of a can of beans is raised from 50 cents to 60 cents, what is the percent increase in the price?",
    choices: ["83.3%", "20%", "18.2%", "16.7%", "10%"], correct: 1, picked: [2, 16, 5, 4, 72], why: "It went up 10 cents out of 50.\n10 ÷ 50 = 20%. 72% picked 10%." }),
  r({ grade: 8, year: 2024, naepId: "2024-8M5 #9", question: "Mary tossed a fair coin 100 times. The coin landed heads up 60 times and tails up 40 times. What is the probability that the next toss of the coin will land heads up?",
    choices: ["1/100", "2/5", "1/2", "3/5", "2/3"], correct: 2, picked: [11, 13, 26, 36, 14], why: "Coins don't remember!\nEvery toss is still 1/2. 36% picked 3/5." }),
  r({ grade: 8, year: 1992, naepId: "1992-8M15 #10", question: "A certain reference file contains approximately one billion facts. About how many millions is that?",
    choices: ["1,000,000", "100,000", "10,000", "1,000", "100"], correct: 3, picked: [40, 10, 5, 22, 23], why: "1 billion = 1,000 millions.\n40% picked 1,000,000." }),
  r({ grade: 8, year: 2013, naepId: "2013-8M7 #15", question: "Mary draws a circle and a square on a piece of paper. What is the greatest possible number of points of intersection between the circle and square?",
    choices: ["2", "4", "6", "8", "10"], correct: 3, picked: [13, 54, 9, 19, 3], why: "Each side of the square can cross the circle twice.\n4 sides × 2 = 8. Most said 4." }),
  r({ grade: 8, year: 1990, naepId: "1990-8M7 #15", question: "The length of a rectangle is 3 more than its width. If L represents the length, what is an expression for the width?",
    choices: ["3 ÷ L", "L ÷ 3", "L × 3", "L + 3", "L − 3"], correct: 4, picked: [9, 9, 38, 29, 14], why: "The width is 3 less than the length: L − 3.\n38% picked L × 3." }),
  r({ grade: 12, year: 1990, naepId: "1990-12M9 #7", question: "A contractor is building 5 different model homes on 5 adjacent lots on one side of a street. If 1 house is to be built on each lot, how many different arrangements of the 5 houses are possible?",
    choices: ["120", "60", "25", "10", "5"], correct: 0, picked: [10, 4, 50, 6, 28], why: "5 choices for the first lot, then 4, 3, 2, 1:\n5 × 4 × 3 × 2 × 1 = 120. Half picked 25." }),
];
