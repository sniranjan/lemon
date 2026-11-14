// Challenge reels: a parent stops scrolling, asks the kid next to them, and comments the answer.
// One question at a time with a draining timer, then the answer. Branding stays small: a logo at the top,
// and on each answer the level it comes from.
import React from "react";
import { AbsoluteFill, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BY_SLUG, CORAL, CREAM, EndCard, HAND, HEAD, INK, Logo, Rich, SAFE } from "./brand";

export type Choice = { label?: string; pic?: string };
export type Question = {
  tag?: string; // chip over the question, e.g. "Age 7"
  bonus?: boolean; // the stretch question: "Bonus ⭐" chip, so a miss is fine
  prompt: string; // the question, e.g. "What comes next?"
  pic?: string; // one big picture above the choices
  row?: { pic: string; n: number }; // a row of pictures to count
  big?: string; // big line; a "?" in it is where the answer appears (no "?": the answer shows under it)
  choices?: Choice[]; // or choices (words or pictures); `correct` is the right one's index
  correct?: number;
  answer?: string; // replaces the "?" in `big`
  note?: string; // one short line after the answer
  level: string; // the level this skill comes from (shown with the answer)
};
export type ChallengeSpec = {
  id: string;
  bg: string;
  hook: string[]; // big lines on the first frame
  hookSub: string;
  mascot?: string; // level slug: its mascot on the first frame
  topic?: string; // topic chip on the first frame, e.g. "Times tables"
  seconds: number; // timer per question
  questions: Question[];
  outro: string[]; // the comment prompt
  levelPrefix?: string; // before the level chip on each answer, e.g. "Our "
  closing?: { line: string; sub: string }; // a brand card after the outro
};

const INTRO = 10;
const REVEAL = 42;
const HOOK = 66;
const OUTRO = 90;
export const qFrames = (s: ChallengeSpec) => INTRO + s.seconds * 30 + REVEAL;
const CLOSING = 120;
export const challengeFrames = (s: ChallengeSpec) => HOOK + s.questions.length * qFrames(s) + OUTRO + (s.closing ? CLOSING : 0);

const GREEN = "#2fa35a";

// Springs that start at 70% so the very first frame is never empty (it is the reel's thumbnail).
const usePop = (delay = 0) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return 0.7 + 0.3 * spring({ frame: frame - delay, fps, config: { damping: 11 } });
};

const Pic: React.FC<{ slug: string; size: number }> = ({ slug, size }) => (
  <Img src={staticFile(`pictures/${slug}.svg`)} style={{ width: size, height: size }} />
);

const TopBar: React.FC<{ i: number; n: number }> = ({ i, n }) => (
  <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
    <Logo width={540} />
    <div style={{ display: "flex", gap: 14 }}>
      {Array.from({ length: n }).map((_, k) => (
        <div key={k} style={{ width: k === i ? 54 : 22, height: 22, borderRadius: 11, background: k <= i ? INK : "rgba(31,42,68,.22)" }} />
      ))}
    </div>
  </div>
);

const Timer: React.FC<{ frame: number; total: number }> = ({ frame, total }) => {
  const left = Math.max(0, total - frame);
  const sec = Math.ceil(left / 30);
  const frac = left / total;
  const tick = 1 + 0.12 * Math.max(0, 1 - ((total - left) % 30) / 8);
  return (
    <div style={{ position: "absolute", top: 1360, left: SAFE.side + 20, right: SAFE.side + 20, display: "flex", alignItems: "center", gap: 28 }}>
      <div style={{ ...HEAD, fontSize: 96, width: 110, textAlign: "center", transform: `scale(${left > 0 ? tick : 1})`, color: sec <= 1 && left > 0 ? CORAL : INK }}>
        {left > 0 ? sec : "⏰"}
      </div>
      <div style={{ flex: 1, height: 40, borderRadius: 20, background: "rgba(255,255,255,.7)", border: `5px solid ${INK}`, overflow: "hidden" }}>
        <div style={{ width: `${frac * 100}%`, height: "100%", background: frac < 0.34 ? CORAL : INK }} />
      </div>
    </div>
  );
};

const BigLine: React.FC<{ text: string; answer?: string; reveal: number }> = ({ text, answer, reveal }) => {
  const parts = text.split("?");
  const size = text.length > 14 ? 104 : 140;
  return (
    <div style={{ ...HEAD, fontSize: size, textAlign: "center", whiteSpace: "nowrap" }}>
      {parts.map((p, k) => (
        <React.Fragment key={k}>
          <Rich text={p} />
          {k < parts.length - 1 ? (
            reveal > 0 && answer ? (
              <span style={{ color: CORAL, display: "inline-block", transform: `scale(${0.6 + 0.4 * reveal})` }}><Rich text={answer} /></span>
            ) : (
              <span style={{ display: "inline-block", minWidth: size * 0.9, border: `6px dashed ${INK}`, borderRadius: 24, padding: "0 18px", lineHeight: 1.1 }}>?</span>
            )
          ) : null}
        </React.Fragment>
      ))}
    </div>
  );
};

const Choices: React.FC<{ q: Question; reveal: number }> = ({ q, reveal }) => {
  const cs = q.choices ?? [];
  const pics = cs.every((c) => c.pic);
  if (!pics && cs.length === 2) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 30, marginTop: 30 }}>
        {cs.map((c, k) => {
          const right = k === q.correct;
          const on = reveal > 0 && right;
          return (
            <React.Fragment key={k}>
              {k === 1 ? <div style={{ ...HAND, fontSize: 80 }}>or</div> : null}
              <div style={{
                width: 360, height: 330, background: "#fff", borderRadius: 40, position: "relative",
                border: `7px solid ${on ? GREEN : INK}`, boxShadow: `12px 12px 0 ${on ? GREEN : INK}`,
                display: "flex", alignItems: "center", justifyContent: "center", ...HEAD, fontSize: 130,
                opacity: reveal > 0 && !right ? 1 - 0.6 * reveal : 1, transform: `scale(${on ? 1 + 0.08 * reveal : 1})`,
              }}>
                <Rich text={c.label ?? ""} />
                {on ? <div style={{ position: "absolute", right: -22, top: -28, width: 96, height: 96, borderRadius: 48, background: GREEN, color: "#fff", ...HEAD, fontSize: 66, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${reveal})` }}>✓</div> : null}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    );
  }
  const cols = pics && cs.length === 4 ? 2 : 1;
  const w = cols === 2 ? 400 : 820;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 30, justifyContent: "center", width: 860 }}>
      {cs.map((c, k) => {
        const right = k === q.correct;
        const dim = reveal > 0 && !right ? 1 - 0.65 * reveal : 1;
        return (
          <div key={k} style={{
            width: w, height: pics ? (cols === 2 ? 300 : 200) : 150, background: "#fff", borderRadius: 34,
            border: `6px solid ${reveal > 0 && right ? GREEN : INK}`, boxShadow: `10px 10px 0 ${reveal > 0 && right ? GREEN : INK}`,
            display: "flex", alignItems: "center", justifyContent: pics && cols === 2 ? "center" : "flex-start", gap: 34, padding: "0 40px",
            opacity: dim, transform: `scale(${reveal > 0 && right ? 1 + 0.06 * reveal : 1})`, position: "relative",
          }}>
            {pics ? null : <div style={{ ...HEAD, fontSize: 60, color: CORAL }}>{"ABCD"[k]}</div>}
            {c.pic ? <Pic slug={c.pic} size={cols === 2 ? 220 : 150} /> : null}
            {c.label ? <div style={{ ...HEAD, fontSize: pics ? 70 : 64 }}><Rich text={c.label} /></div> : null}
            {reveal > 0 && right ? (
              <div style={{ position: "absolute", right: -18, top: -24, width: 86, height: 86, borderRadius: 43, background: GREEN, color: "#fff", ...HEAD, fontSize: 60, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${reveal})` }}>✓</div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
};

const QuestionScene: React.FC<{ s: ChallengeSpec; i: number }> = ({ s, i }) => {
  const q = s.questions[i];
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = s.seconds * 30;
  const t = frame - INTRO;
  const reveal = spring({ frame: frame - INTRO - total, fps, config: { damping: 12 } });
  const pop = usePop(0);
  const lv = BY_SLUG[q.level];
  return (
    <AbsoluteFill style={{ background: s.bg }}>
      <TopBar i={i} n={s.questions.length} />
      <div style={{ position: "absolute", top: 330, height: 990, left: SAFE.side, right: SAFE.side, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: q.pic && q.choices ? 26 : 40, transform: `scale(${pop})` }}>
        {q.bonus ? <div style={{ ...HEAD, fontSize: 56, background: CORAL, color: "#fff", borderRadius: 999, padding: "10px 40px" }}>Bonus ⭐</div>
          : q.tag ? <div style={{ ...HEAD, fontSize: 52, background: INK, color: "#fff", borderRadius: 999, padding: "10px 40px" }}>{q.tag}</div> : null}
        <div style={{ ...HEAD, fontSize: 86, textAlign: "center" }}><Rich text={q.prompt} /></div>
        {q.pic ? <div style={{ background: "#fff", borderRadius: 40, border: `6px solid ${INK}`, padding: q.choices ? 14 : 20 }}><Pic slug={q.pic} size={q.choices ? 190 : 300} /></div> : null}
        {q.row ? (
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 16, width: 880 }}>
            {Array.from({ length: q.row.n }).map((_, k) => <Pic key={k} slug={q.row!.pic} size={q.row!.n > 5 ? 150 : 170} />)}
          </div>
        ) : null}
        {q.big ? <div style={{ marginTop: 30 }}><BigLine text={q.big} answer={q.answer} reveal={reveal} /></div> : null}
        {q.big && !q.big.includes("?") && q.answer && reveal > 0 ? (
          <div style={{ ...HEAD, fontSize: 100, color: CORAL, transform: `scale(${0.6 + 0.4 * reveal})` }}><Rich text={q.answer} /></div>
        ) : null}
        {q.choices ? <Choices q={q} reveal={reveal} /> : null}
        {q.note && reveal > 0 ? <div style={{ ...HAND, fontSize: 60, color: INK, textAlign: "center", opacity: reveal }}><Rich text={q.note} /></div> : null}
      </div>
      {reveal > 0.05 ? (
        <div style={{ position: "absolute", top: 1392, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: reveal }}>
          <div style={{ display: "flex", alignItems: "center", gap: 18, background: CREAM, border: `5px solid ${INK}`, borderRadius: 999, padding: "10px 34px 10px 14px" }}>
            <Img src={staticFile(lv.mascot)} style={{ width: 84, height: 84 }} />
            <div style={{ ...HEAD, fontSize: 44 }}>{s.levelPrefix ?? ""}{lv.name} level · age {lv.age}</div>
          </div>
        </div>
      ) : (
        <Timer frame={Math.max(0, t)} total={total} />
      )}
    </AbsoluteFill>
  );
};

const Hook: React.FC<{ s: ChallengeSpec }> = ({ s }) => {
  const a = usePop(0);
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: s.bg, alignItems: "center", justifyContent: "center", paddingBottom: 240 }}>
      <div style={{ position: "absolute", top: 80 }}><Logo width={540} /></div>
      {s.mascot ? (
        <div style={{ width: 300, height: 300, borderRadius: 150, background: "#fff", border: `7px solid ${INK}`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 50, transform: `scale(${a})` }}>
          <Img src={staticFile(BY_SLUG[s.mascot].mascot)} style={{ width: 230, height: 230 }} />
        </div>
      ) : null}
      {s.topic ? <div style={{ ...HEAD, fontSize: 70, background: INK, color: "#fff", borderRadius: 999, padding: "12px 48px", marginBottom: 40, transform: `scale(${a})` }}>{s.topic}</div> : null}
      <div style={{ ...HEAD, fontSize: 124, textAlign: "center", transform: `scale(${a})`, padding: `0 ${SAFE.side}px` }}>
        {s.hook.map((l, k) => <div key={k}>{l}</div>)}
      </div>
      <div style={{ ...HAND, fontSize: 64, marginTop: 44, textAlign: "center", whiteSpace: "pre-line", opacity: interpolate(frame, [0, 10], [0.6, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        {s.hookSub}
      </div>
    </AbsoluteFill>
  );
};

const Outro: React.FC<{ s: ChallengeSpec }> = ({ s }) => {
  const a = usePop(0);
  return (
    <AbsoluteFill style={{ background: CREAM, alignItems: "center", justifyContent: "center", paddingBottom: 260 }}>
      <div style={{ ...HEAD, fontSize: 110, textAlign: "center", transform: `scale(${a})`, padding: `0 ${SAFE.side}px` }}>
        {s.outro.map((l, k) => <div key={k}>{l}</div>)}
      </div>
      <div style={{ ...HAND, fontSize: 62, color: CORAL, marginTop: 40 }}>a new one every day · follow along</div>
      <div style={{ marginTop: 70 }}><Logo width={420} /></div>
    </AbsoluteFill>
  );
};

export const Challenge: React.FC<{ spec: ChallengeSpec }> = ({ spec }) => (
  <AbsoluteFill style={{ background: spec.bg }}>
    <Sequence durationInFrames={HOOK}><Hook s={spec} /></Sequence>
    {spec.questions.map((_, i) => (
      <Sequence key={i} from={HOOK + i * qFrames(spec)} durationInFrames={qFrames(spec)}><QuestionScene s={spec} i={i} /></Sequence>
    ))}
    <Sequence from={HOOK + spec.questions.length * qFrames(spec)} durationInFrames={OUTRO}><Outro s={spec} /></Sequence>
    {spec.closing ? (
      <Sequence from={HOOK + spec.questions.length * qFrames(spec) + OUTRO}><EndCard line={spec.closing.line} sub={spec.closing.sub} /></Sequence>
    ) : null}
  </AbsoluteFill>
);
