// Write sample gift card PDFs to look at: npx tsx scripts/gift-card/sample.ts <out dir>
import { writeFileSync } from "node:fs";
import { giftCardPdf, type CardGift } from "../../worker/giftCard";

const out = process.argv[2] ?? ".";
const message300 =
  "Happy birthday! We hope these pages bring lots of quiet mornings, giggles over counting games and proud moments reading the first words aloud. " +
  "Take it slow, a few pages a day, and keep the ones you love on the fridge. We can't wait to hear what you learn next. Lots of love from all of us!!!";
const samples: Record<string, CardGift> = {
  normal: {
    kind: "all",
    amountCents: 9900,
    code: "HAPY-BDAY-MAYA",
    childName: "Maya",
    buyerName: "Priya",
    message: "Happy birthday, Maya! A little something for rainy afternoons.",
  },
  empty: { kind: "credit", amountCents: 2900, code: "ABCD-EFGH-JKMN", childName: null, buyerName: null, message: null },
  longest: {
    kind: "credit",
    amountCents: 25000,
    code: "WWWW-WWWW-WWWW",
    childName: "W".repeat(30),
    buyerName: "W".repeat(60),
    message: message300.slice(0, 300),
  },
};
const t0 = performance.now();
for (const [name, g] of Object.entries(samples)) writeFileSync(`${out}/card-${name}.pdf`, await giftCardPdf(g));
console.log(`${Object.keys(samples).length} cards in ${Math.round(performance.now() - t0)} ms`);
