// Order emails, sent through Cloudflare's send_email binding from hello@paperlessons.com
// (Fastmail receives replies; Cloudflare signs outgoing mail for paperlessons.com).

export const FROM = { name: "paperlessons", email: "hello@paperlessons.com" };

/** "2026-11-13 14:41:14" (D1, UTC) → "November 13, 2026". */
export function longDate(sqlUtc: string): string {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(new Date(`${sqlUtc.replace(" ", "T")}Z`));
}

const esc = (s: string) => s.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]!);

export async function sendOrderEmail(
  mailer: SendEmail | undefined,
  o: { to: string; levelName: string; levelTitle: string; url: string; expiresAt: string },
): Promise<void> {
  if (!mailer) return;
  const until = longDate(o.expiresAt);
  const subject = `Your ${o.levelName} pages are ready to download`;
  const text = [
    `Thank you for buying ${o.levelName} (${o.levelTitle}).`,
    "",
    `Download your PDFs here: ${o.url}`,
    "",
    `This link works for 7 days, until ${until}. After that it expires, so download and save your files now.`,
    "Please don't share the link or the files: they're for the children in your home.",
    "",
    "Print a few pages at a time, or all at once. Have fun!",
    "paperlessons · hello@paperlessons.com",
  ].join("\n");
  const html = `<!doctype html><html><body style="margin:0;background:#fff8ec;font-family:Nunito,Arial,sans-serif;color:#1f2a44">
<div style="max-width:520px;margin:0 auto;padding:32px 20px">
  <img src="https://paperlessons.com/brand/logo-email.png" width="200" alt="paperlessons" style="display:block;width:200px;height:auto;border:0">
  <h1 style="font-size:26px;margin:24px 0 8px">Your ${esc(o.levelName)} pages are ready</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">Thank you for buying <b>${esc(o.levelName)}</b> (${esc(o.levelTitle)}).
  Your printable PDFs and answer keys are waiting on your download page.</p>
  <p style="margin:0 0 24px"><a href="${esc(o.url)}" style="display:inline-block;background:#1f2a44;color:#fff;text-decoration:none;font-weight:800;font-size:17px;padding:12px 22px;border-radius:999px">Download your PDFs</a></p>
  <p style="font-size:15px;line-height:1.5;background:#ffefc2;border-radius:12px;padding:12px 14px;margin:0 0 20px">
  <b>This link works for 7 days, until ${esc(until)}.</b> After that it expires, so download and save your files now.
  Please don't share the link or the files: they're for the children in your home.</p>
  <p style="font-size:14px;color:#5b6478;line-height:1.5;margin:0">Questions? Just reply to this email.<br>paperlessons · hello@paperlessons.com</p>
</div></body></html>`;
  try {
    await mailer.send({ from: FROM, to: o.to, replyTo: FROM, subject, text, html });
  } catch (e) {
    console.error("order email failed", e);
  }
}
