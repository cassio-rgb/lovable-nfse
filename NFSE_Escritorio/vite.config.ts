// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

// Office-local profile (sdd/design-addendum-002): opt-in only via NFSE_BUILD_PROFILE=local-node,
// set by scripts/escritorio.py. Default Lovable/Cloudflare build is untouched when unset.
const localNode = process.env["NFSE_BUILD_PROFILE"] === "local-node";

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
  ...(localNode
    ? { nitro: { preset: "node-server", output: { dir: ".output-local" } } }
    : {}),
});
