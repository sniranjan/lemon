// Session replay (OpenReplay, self-hosted at replay.cloudhut.io). The user asked for nothing to be
// masked: text, inputs (emails, numbers, dates) and network payloads are all recorded as-is.
// Runs only on the real site, so local dev and test runs don't create sessions.
import { tracker } from "@openreplay/tracker";

let started = false;

/** Called via startTracking() in consent.ts, which checks the visitor's cookie choice first. */
export function startReplay() {
  if (started || location.hostname !== "paperlessons.com") return;
  started = true;
  try {
    tracker.configure({
      projectKey: "rwtuupd5Hv1QVJwXGKro",
      ingestPoint: "https://replay.cloudhut.io/ingest",
      // no masking anywhere
      defaultInputMode: 0, // 0 = plain
      obscureTextEmails: false,
      obscureTextNumbers: false,
      obscureInputEmails: false,
      obscureInputNumbers: false,
      obscureInputDates: false,
      network: {
        capturePayload: true,
        failuresOnly: false,
        ignoreHeaders: false,
        sessionTokenHeader: false,
        captureInIframes: true,
      },
    });
    tracker.start();
  } catch (e) {
    console.warn("replay failed to start", e);
  }
}

/** Stop recording (gift-code pages). */
export function stopReplay() {
  if (!started) return;
  try {
    tracker.stop();
  } catch {
    /* ignore */
  }
}
