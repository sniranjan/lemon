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
  // Every name is optional: a gift with none still reads naturally ("Hi there", no "from" line).
  buyerName: string | null;
  recipientName: string | null;
  childName: string | null;
  message: string | null;
};

const box = (inner: string) =>
  `<div style="font-size:16px;line-height:1.55;background:#fff;border:3px solid #1f2a44;border-radius:16px;padding:14px 16px;margin:0 0 20px">${inner}</div>`;

/**
 * To the buyer, once paid: a receipt and the share kit (the code, the gift card link and a ready-to-forward
 * message), so they can pass the gift on however they like. Emailed gifts also say when the email goes out.
 * Never any download links: the files are for the family who gets the gift.
 */
export async function sendGiftBuyerEmail(
  mailer: SendEmail | undefined,
  g: GiftEmail & { to: string; amount: string; cardUrl: string; shareText: string; deliverOn: string | null; sentNow: boolean },
): Promise<boolean> {
  if (!mailer) return false;
  const name = g.recipientName;
  const them = name ?? "them";
  const forWhom = g.childName || name;
  const when = g.deliverOn
    ? g.sentNow
      ? `We've just emailed ${them} your message and a link to open the gift. You can also share it yourself below.`
      : `We'll email ${them} your message and a link to open the gift on ${longDate(g.deliverOn)}. Want to share it sooner? Everything you need is below.`
    : "It's yours to give: send the link below by text, WhatsApp or email, or print the card and tuck it into a birthday card.";
  const subject = g.deliverOn
    ? name ? `Your gift for ${name} is ready` : "Your gift is ready"
    : name ? `Your gift for ${name} is ready to share` : "Your gift is ready to share";
  const thanks = `Thank you! You gave ${forWhom ? `${forWhom} ` : "a gift of "}${g.what} (${g.amount}).`;
  const text = [
    thanks,
    "",
    when,
    "",
    `Gift code: ${g.code}`,
    `Gift card (open, share or print): ${g.cardUrl}`,
    "",
    "Ready to forward:",
    g.shareText,
    "",
    "The code never expires. All sales are final: gifts can't be refunded or exchanged for cash.",
    "",
    "Paper Lessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(
    `  <h1 style="font-size:26px;margin:24px 0 8px">${esc(subject)}</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 12px">${esc(thanks)}</p>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">${esc(when)}</p>
  <p style="font-size:15px;margin:0 0 4px">Gift code</p>
  <p style="font-family:Menlo,Consolas,monospace;font-size:24px;font-weight:800;letter-spacing:2px;margin:0 0 20px">${esc(g.code)}</p>
  <p style="font-size:15px;margin:0 0 4px">Gift card link</p>
  <p style="font-size:16px;margin:0 0 16px"><a href="${esc(g.cardUrl)}" style="color:#e4572e;font-weight:800">${esc(g.cardUrl)}</a></p>
  ${button(g.cardUrl, "Open, share or print the card")}
  <p style="font-size:15px;font-weight:800;margin:0 0 6px">Ready to forward</p>
  ${box(esc(g.shareText))}
  <p style="font-size:15px;line-height:1.5;background:#ffefc2;border-radius:12px;padding:12px 14px;margin:0 0 20px">
  The code never expires. All sales are final: gifts can't be refunded or exchanged for cash.</p>`,
    "Paper Lessons",
  );
  return send(mailer, GIFT_FROM, g.to, subject, text, html, "gift receipt");
}

/** To the recipient, on the delivery date (emailed gifts only): the buyer's message and a link to open the gift. */
export async function sendGiftRecipientEmail(
  mailer: SendEmail | undefined,
  g: GiftEmail & { to: string; redeemUrl: string },
): Promise<boolean> {
  if (!mailer) return false;
  const from = g.buyerName;
  const subject = from ? `${from} sent you a gift from Paper Lessons` : "You've been sent a gift from Paper Lessons";
  const hi = g.recipientName ? `Hi ${g.recipientName}` : "Hi there";
  const forWhom = g.childName ? `for you and ${g.childName}` : "for you";
  const lead = `${from ? `${from} sent a gift` : "Here's a gift"} ${forWhom}`;
  const text = [
    `${hi},`,
    "",
    `${lead}: ${g.what} of Paper Lessons, printable reading and math pages for kids.`,
    ...(g.message ? ["", g.message, ...(from ? [`- ${from}`] : [])] : []),
    "",
    `Open your gift: ${g.redeemUrl}`,
    `Gift code: ${g.code}. It never expires, so open it whenever you're ready.`,
    "",
    "Paper Lessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(
    `  <h1 style="font-size:26px;margin:24px 0 8px">${from ? `${esc(from)} sent you a gift` : "You've been sent a gift"}</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">${esc(hi)}! ${esc(lead)}:
  <b>${esc(g.what)}</b> of Paper Lessons, printable reading and math pages for kids.</p>
  ${g.message ? box(`<span style="font-size:17px">${paragraphs(g.message)}</span>${from ? `<br><span style="color:#5b6478">- ${esc(from)}</span>` : ""}`) : ""}
  ${button(g.redeemUrl, "Open your gift")}
  <p style="font-size:15px;line-height:1.5;margin:0 0 20px">Gift code: <b style="font-family:Menlo,Consolas,monospace;letter-spacing:1px">${esc(g.code)}</b><br>
  It never expires, so open it whenever you're ready.</p>`,
    "Paper Lessons",
  );
  return send(mailer, GIFT_FROM, g.to, subject, text, html, "gift");
}
