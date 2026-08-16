import React from "react";
import { AbsoluteFill } from "remotion";
import { CutawaySceneView } from "./components/CutawayLayer";
import type { TimelineCutaway } from "./types";

/**
 * Part 4 buku-kas fixture — episode data, not framework defaults.
 * Cues are cam word times minus the 406.40s scene start.
 */
export const LAB_CUTAWAY: TimelineCutaway = {
  id: "lab-document-ledger",
  scene: "receipt_tape",
  family: "document",
  intent: "prove",
  tone: "tactile",
  fromSec: 0,
  durationSec: 21.2,
  kicker: "Buku kas",
  title: "Tercatat otomatis",
  openingBalance: 1200000,
  copy: {
    kicker: "Buku kas",
    title: "Tercatat otomatis",
    totalLabel: "Saldo berjalan",
    lockLabel: "Tidak bisa diedit",
    stampLabel: "TERVALIDASI",
    attemptLabels: ["Edit", "Hapus"],
    inLabel: "Masuk",
    outLabel: "Keluar",
  },
  feeds: [
    { label: "Penjualan", amount: 4850000, atSec: 6.54, icon: "cart" },
    { label: "Pembelian", amount: -2300000, atSec: 7.7, icon: "bag" },
    {
      label: "Biaya operasional",
      amount: -250000,
      atSec: 8.74,
      icon: "receipt",
    },
  ],
  cues: {
    ledgerInSec: 0.14,
    inOutSec: 4.12,
    balanceSec: 10.12,
    lockSec: 13.34,
    attemptSec: [15.94, 16.62],
    stampSec: 19.56,
  },
  inLabel: "Masuk",
  outLabel: "Keluar",
  lockLabel: "Tidak bisa diedit",
  attemptLabels: ["Edit", "Hapus"],
  stampLabel: "TERVALIDASI",
  balanceLabel: "Saldo berjalan",
};

/** Minimal-family smoke fixture for CutawayLab matrix. */
export const LAB_MINIMAL: TimelineCutaway = {
  id: "lab-minimal",
  scene: "minimal",
  family: "minimal",
  intent: "summarize",
  fromSec: 0,
  durationSec: 6,
  copy: { kicker: "Claim", title: "One strong idea" },
  kicker: "Claim",
  title: "One strong idea",
  cues: { openSec: 0.1, ledgerInSec: 0.1 },
};

export const CutawayLab: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => (
  <AbsoluteFill>
    <CutawaySceneView cutaway={cutaway} />
  </AbsoluteFill>
);
