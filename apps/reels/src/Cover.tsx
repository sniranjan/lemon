// Story highlight cover, one per level: the mascot in a white disc on the level color (Instagram crops a circle).
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { BY_SLUG, INK } from "./brand";

export const Cover: React.FC<{ slug: string }> = ({ slug }) => {
  const lv = BY_SLUG[slug];
  return (
    <AbsoluteFill style={{ background: lv.color, alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 760, height: 760, borderRadius: 380, background: "#fff", border: `16px solid ${INK}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Img src={staticFile(lv.mascot)} style={{ width: 560, height: 560 }} />
      </div>
    </AbsoluteFill>
  );
};
