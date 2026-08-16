import React from "react";
import { AbsoluteFill } from "remotion";
import { CutawaySceneView } from "./components/CutawayLayer";
import type { TimelineCutaway } from "./types";

/**
 * Scene lab: preview one MG cutaway without staging media, so cue timing can be
 * checked frame by frame before it goes into an episode cover.
 *
 * Cues below are Part 4 cam word times minus the 406.40s scene start:
 * "buku kas" 406.54 · "masuk/keluar" 410.52 · "penjualan" 412.94 ·
 * "pembelian" 414.10 · "operasional" 415.14 · "saldo berjalan" 416.52 ·
 * "immutable ledger" 419.74 · "diedit" 422.34 · "dibusyap" 423.02 ·
 * "tervalidasi" 425.96
 */
export const LAB_CUTAWAY: TimelineCutaway = {
  id: "lab-ledger-flow",
  scene: "ledger_flow",
  fromSec: 0,
  durationSec: 21.2,
  kicker: "Buku kas",
  title: "Tercatat otomatis",
  openingBalance: 1200000,
  feeds: [
    { label: "Penjualan", amount: 4850000, atSec: 6.54 },
    { label: "Pembelian", amount: -2300000, atSec: 7.7 },
    { label: "Biaya operasional", amount: -250000, atSec: 8.74 },
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

export const CutawayLab: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => (
  <AbsoluteFill>
    <CutawaySceneView cutaway={cutaway} />
  </AbsoluteFill>
);
