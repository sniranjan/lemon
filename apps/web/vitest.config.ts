// Unit tests for the Worker (node, not workerd): D1 is node:sqlite with our migrations, R2 and email are fakes,
// and Stripe is a stubbed fetch, so no test can reach a real API. Kept apart from vite.config.ts so the
// Cloudflare plugin doesn't load here.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: { include: ["test/**/*.test.ts"], environment: "node" },
});
