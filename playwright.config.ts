/** Three-browser real environmental service acceptance by Jason Stys; variables: docs/CODE_INDEX.md. */
import { defineConfig, devices } from "@playwright/test";
const python =
  process.env.PYTHON ?? (process.platform === "win32" ? ".venv/Scripts/python.exe" : "python");
const external = process.env.EARTH_BASE_URL;
export default defineConfig({
  testDir: "tests",
  testMatch: "ui.spec.ts",
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: "list",
  use: {
    baseURL: external ?? "http://127.0.0.1:8905",
    trace: "off",
    screenshot: "off",
    video: "off",
    reducedMotion: "reduce",
  },
  ...(external
    ? {}
    : {
        webServer: {
          command: `"${python}" -m eostudio serve --port 8905 --no-browser`,
          url: "http://127.0.0.1:8905/api/health",
          reuseExistingServer: false,
          timeout: 20000,
        },
      }),
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
