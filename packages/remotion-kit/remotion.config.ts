import { existsSync } from "node:fs";
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

const binariesDir = process.env.REMOTION_BINARIES_DIR;
if (binariesDir) {
  const remotionBin =
    process.platform === "win32"
      ? `${binariesDir}\\remotion.exe`
      : `${binariesDir}/remotion`;
  // Only override when compositor binaries were staged — an empty dir breaks chmod.
  if (existsSync(remotionBin)) {
    Config.setBinariesDirectory(binariesDir);
  }
}

// The default 30s delay-render timeout is too tight for `still` renders:
// each `still` invocation cold-starts its own dev/proxy server, and the
// very first `Fetching .../proxy?src=...cam.mp4` request can stall past
// 30s while that server warms up — especially when `ae mg-review` fires
// many `still` calls back-to-back (e.g. one per MG overlay). Seen in
// production as flaky "waiting for the page to render the React
// component failed: timeout 33000ms exceeded" failures that vanish on
// retry. Give it more room instead of relying on retries.
Config.setDelayRenderTimeoutInMilliseconds(90000);
