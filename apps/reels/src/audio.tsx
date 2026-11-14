// Sound for the reels: a quiet music bed plus our own tick / ding effects (synthesized, no license needed).
// Music: Kevin MacLeod (incompetech.com), CC BY 4.0 — every caption that uses a track carries its credit line.
// Files live in public/audio (git-ignored; scripts/marketing/reel_assets.py downloads them).
import React from "react";
import { Audio, Sequence, interpolate, staticFile } from "remotion";

// gain brings each track to about -24 LUFS: a bed under the ticks, never loud (measured with ffmpeg ebur128).
export const TRACKS = {
  "easy-lemon": { title: "Easy Lemon", gain: 0.39 },
  carefree: { title: "Carefree", gain: 0.62 },
  "thinking-music": { title: "Thinking Music", gain: 0.65 },
  wallpaper: { title: "Wallpaper", gain: 0.23 },
} as const;
export type Track = keyof typeof TRACKS;
export const DEFAULT_TRACK: Track = "carefree";

export const credit = (t: Track) =>
  `Music: "${TRACKS[t].title}" Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0 (creativecommons.org/licenses/by/4.0/)`;

export const Music: React.FC<{ track: Track; frames: number }> = ({ track, frames }) => {
  const g = TRACKS[track].gain;
  return (
    <Audio
      src={staticFile(`audio/${track}.mp3`)}
      loop
      volume={(f) => g * interpolate(f, [0, 12, frames - 30, frames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
    />
  );
};

// One soft tick per second of the timer (tock on the last second), then a ding when the answer shows.
export const TimerSounds: React.FC<{ start: number; seconds: number }> = ({ start, seconds }) => (
  <>
    {Array.from({ length: seconds }).map((_, k) => (
      <Sequence key={k} from={start + k * 30} durationInFrames={10}>
        <Audio src={staticFile(k === seconds - 1 ? "audio/tock.wav" : "audio/tick.wav")} volume={0.75} />
      </Sequence>
    ))}
    <Sequence from={start + seconds * 30} durationInFrames={45}>
      <Audio src={staticFile("audio/ding.wav")} volume={1} />
    </Sequence>
  </>
);
