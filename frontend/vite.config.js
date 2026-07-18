import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, host: true },
  // TEMP (debugging a prod-only "n is not a function"): keep readable names so
  // the runtime error points at the real function. Revert to minified after fix.
  build: { minify: false },
});
