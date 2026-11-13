import React from "react";
import { Composition } from "remotion";
import { Challenge, challengeFrames } from "./Challenge";
import { Cover } from "./Cover";
import { LEVELS } from "./brand";
import { CHALLENGES, topicReel } from "./challenges";
import { TOPICS_MIDDLE } from "./topics/middle";
import { TOPICS_TEEN } from "./topics/teen";
import { TOPICS_UPPER } from "./topics/upper";
import { TOPICS_YOUNG } from "./topics/young";

export const TOPIC_REELS = [...TOPICS_YOUNG, ...TOPICS_MIDDLE, ...TOPICS_UPPER, ...TOPICS_TEEN].map(topicReel);
import { LADDER_FRAMES, Ladder } from "./Ladder";
import { QUIZ_FRAMES, Quiz } from "./Quiz";
import { STACK_FRAMES, Stack } from "./Stack";

const reel = { fps: 30, width: 1080, height: 1920 };

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Ladder" component={Ladder} durationInFrames={LADDER_FRAMES} {...reel} />
    <Composition id="Quiz" component={Quiz} durationInFrames={QUIZ_FRAMES} {...reel} />
    <Composition id="Stack" component={Stack} durationInFrames={STACK_FRAMES} {...reel} />
    {CHALLENGES.map((spec) => (
      <Composition key={spec.id} id={spec.id} component={Challenge} defaultProps={{ spec }} durationInFrames={challengeFrames(spec)} {...reel} />
    ))}
    {TOPIC_REELS.map((spec) => (
      <Composition key={spec.id} id={spec.id} component={Challenge} defaultProps={{ spec }} durationInFrames={challengeFrames(spec)} {...reel} />
    ))}
    {LEVELS.map((l) => (
      <Composition key={l.slug} id={`Cover-${l.slug}`} component={Cover} defaultProps={{ slug: l.slug }} durationInFrames={1} {...reel} />
    ))}
  </>
);
