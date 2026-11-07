// Order and gift emails, sent through Cloudflare's send_email binding from hello@paperlessons.com
// (Fastmail receives replies; Cloudflare signs outgoing mail for paperlessons.com).
// Senders return true once the message was handed to Cloudflare, false if there's no mailer or it failed.

export const FROM = { name: "paperlessons", email: "hello@paperlessons.com" };
/** Gift emails come from "Paper Lessons". The buyer's name only ever appears in the message, never in From. */
export const GIFT_FROM = { name: "Paper Lessons", email: "hello@paperlessons.com" };

/** "2026-11-13 14:41:14" (D1, UTC) or "2026-11-13" → "November 13, 2026". */
export function longDate(sqlUtc: string): string {
  const iso = sqlUtc.length === 10 ? `${sqlUtc}T12:00:00` : sqlUtc.replace(" ", "T");
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(new Date(`${iso}Z`));
}

export const esc = (s: string) => s.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]!);

/** Message text for HTML: escaped, line breaks kept. */
const paragraphs = (s: string) => esc(s).replace(/\n/g, "<br>");

const shell = (body: string, sign = "paperlessons") => `<!doctype html><html><body style="margin:0;background:#fff8ec;font-family:Nunito,Arial,sans-serif;color:#1f2a44">
<div style="max-width:520px;margin:0 auto;padding:32px 20px">
  <img src="https://paperlessons.com/brand/logo-email.png" width="200" alt="paperlessons" style="display:block;width:200px;height:auto;border:0">
${body}
  <p style="font-size:14px;color:#5b6478;line-height:1.5;margin:0">Questions? Just reply to this email.<br>${sign} · hello@paperlessons.com</p>
</div></body></html>`;

const button = (href: string, label: string) =>
  `<p style="margin:0 0 24px"><a href="${esc(href)}" style="display:inline-block;background:#1f2a44;color:#fff;text-decoration:none;font-weight:800;font-size:17px;padding:12px 22px;border-radius:999px">${esc(label)}</a></p>`;

async function send(mailer: SendEmail, from: typeof FROM, to: string, subject: string, text: string, html: string, what: string) {
  try {
    await mailer.send({ from, to, replyTo: from, subject, text, html });
    return true;
  } catch (e) {
    console.error(`${what} email failed`, e);
    return false;
  }
}

/** The download link for an order (bought, or opened with a gift: `gift` changes the thank-you line). */
export async function sendOrderEmail(
  mailer: SendEmail | undefined,
  o: { to: string; levelName: string; levelTitle: string; url: string; expiresAt: string; gift?: boolean },
): Promise<boolean> {
  if (!mailer) return false;
  const until = longDate(o.expiresAt);
  const subject = `Your ${o.levelName} pages are ready to download`;
  const opener = o.gift ? "Here are your gift pages:" : "Thank you for buying";
  const text = [
    `${opener} ${o.levelName} (${o.levelTitle}).`,
    "",
    `Download your PDFs here: ${o.url}`,
    "",
    `This link works for 7 days, until ${until}. After that it expires, so download and save your files now.`,
    "Please don't share the link or the files: they're for the children in your home.",
    "",
    "Print a few pages at a time, or all at once. Have fun!",
    "paperlessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(`  <h1 style="font-size:26px;margin:24px 0 8px">Your ${esc(o.levelName)} pages are ready</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">${opener} <b>${esc(o.levelName)}</b> (${esc(o.levelTitle)}).
  Your printable PDFs and answer keys are waiting on your download page.</p>
  ${button(o.url, "Download your PDFs")}
  <p style="font-size:15px;line-height:1.5;background:#ffefc2;border-radius:12px;padding:12px 14px;margin:0 0 20px">
  <b>This link works for 7 days, until ${esc(until)}.</b> After that it expires, so download and save your files now.
  Please don't share the link or the files: they're for the children in your home.</p>`);
  return send(mailer, FROM, o.to, subject, text, html, "order");
}

export type GiftEmail = {
  code: string;
  what: string; // "every level, ages 3 to 12" or "$50 to spend on any level"
  buyerName: string;
  recipientName: string;
  childName: string | null;
  message: string | null;
};

/**
 * To the buyer, once paid: a receipt and the printable gift card (with the code). Never any download links:
 * the files are for the family who gets the gift.
 */
export async function sendGiftBuyerEmail(
  mailer: SendEmail | undefined,
  g: GiftEmail & { to: string; amount: string; cardUrl: string; deliverOn: string; sentNow: boolean },
): Promise<boolean> {
  if (!mailer) return false;
  const when = g.sentNow
    ? `We've just emailed ${g.recipientName} your message and a link to open the gift.`
    : `We'll email ${g.recipientName} your message and a link to open the gift on ${longDate(g.deliverOn)}.`;
  const subject = `Your gift for ${g.recipientName} is ready`;
  const text = [
    `Thank you! You gave ${g.recipientName} ${g.what} (${g.amount}).`,
    "",
    when,
    "",
    `Gift code: ${g.code}`,
    `Print the gift card: ${g.cardUrl}`,
    "",
    "Tuck the card into a birthday card if you like. The code never expires.",
    "All sales are final: gifts can't be refunded or exchanged for cash.",
    "",
    "Paper Lessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(
    `  <h1 style="font-size:26px;margin:24px 0 8px">Your gift for ${esc(g.recipientName)} is ready</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 12px">Thank you! You gave <b>${esc(g.recipientName)}</b> ${esc(g.what)} (${esc(g.amount)}).</p>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">${esc(when)}</p>
  <p style="font-size:15px;margin:0 0 4px">Gift code</p>
  <p style="font-family:Menlo,Consolas,monospace;font-size:24px;font-weight:800;letter-spacing:2px;margin:0 0 20px">${esc(g.code)}</p>
  ${button(g.cardUrl, "Print the gift card")}
  <p style="font-size:15px;line-height:1.5;background:#ffefc2;border-radius:12px;padding:12px 14px;margin:0 0 20px">
  Tuck the card into a birthday card if you like. The code never expires.
  All sales are final: gifts can't be refunded or exchanged for cash.</p>`,
    "Paper Lessons",
  );
  return send(mailer, GIFT_FROM, g.to, subject, text, html, "gift receipt");
}

/** To the recipient, on the delivery date: the buyer's message and a link to open the gift. */
export async function sendGiftRecipientEmail(
  mailer: SendEmail | undefined,
  g: GiftEmail & { to: string; redeemUrl: string },
): Promise<boolean> {
  if (!mailer) return false;
  const subject = `${g.buyerName} sent you a gift from Paper Lessons`;
  const forWhom = g.childName ? `for you and ${g.childName}` : "for you";
  const text = [
    `Hi ${g.recipientName},`,
    "",
    `${g.buyerName} sent a gift ${forWhom}: ${g.what} of Paper Lessons, printable reading and math pages for kids.`,
    ...(g.message ? ["", g.message, `- ${g.buyerName}`] : []),
    "",
    `Open your gift: ${g.redeemUrl}`,
    `Gift code: ${g.code}. It never expires, so open it whenever you're ready.`,
    "",
    "Paper Lessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(
    `  <h1 style="font-size:26px;margin:24px 0 8px">${esc(g.buyerName)} sent you a gift</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">Hi ${esc(g.recipientName)}! ${esc(g.buyerName)} sent a gift ${esc(forWhom)}:
  <b>${esc(g.what)}</b> of Paper Lessons, printable reading and math pages for kids.</p>
  ${g.message ? `<div style="font-size:17px;line-height:1.55;background:#fff;border:3px solid #1f2a44;border-radius:16px;padding:14px 16px;margin:0 0 20px">${paragraphs(g.message)}<br><span style="color:#5b6478">- ${esc(g.buyerName)}</span></div>` : ""}
  ${button(g.redeemUrl, "Open your gift")}
  <p style="font-size:15px;line-height:1.5;margin:0 0 20px">Gift code: <b style="font-family:Menlo,Consolas,monospace;letter-spacing:1px">${esc(g.code)}</b><br>
  It never expires, so open it whenever you're ready.</p>`,
    "Paper Lessons",
  );
  return send(mailer, GIFT_FROM, g.to, subject, text, html, "gift");
}
