/**
 * Curated Lucide set for `IllustrationTag` (`note:"icon:<name>"`).
 *
 * Deliberately NOT `import { icons } from "lucide-react"` — that map holds
 * 1807 components and would land in every Remotion render bundle. These are
 * imported by name so webpack tree-shakes to just what's referenced.
 *
 * Unknown names fall back to no icon (spec §3.10), so a typo degrades to a
 * bare word rather than breaking the render. To add one: import it here and
 * add the kebab-case key.
 */
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Braces,
  Check,
  CircleAlert,
  Clock,
  Cpu,
  Database,
  FileText,
  Folder,
  Gauge,
  GitBranch,
  Info,
  Key,
  Lightbulb,
  Lock,
  type LucideIcon,
  Pencil,
  Rocket,
  Search,
  Settings,
  Sparkles,
  Star,
  Terminal,
  ThumbsDown,
  ThumbsUp,
  TrendingDown,
  TrendingUp,
  Wand,
  Wrench,
  Zap,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  "alert-triangle": AlertTriangle,
  "arrow-right": ArrowRight,
  bot: Bot,
  braces: Braces,
  check: Check,
  "circle-alert": CircleAlert,
  clock: Clock,
  cpu: Cpu,
  database: Database,
  "file-text": FileText,
  folder: Folder,
  gauge: Gauge,
  // lucide v1 dropped brand marks; `github` keeps working as an alias.
  "git-branch": GitBranch,
  github: GitBranch,
  info: Info,
  key: Key,
  lightbulb: Lightbulb,
  lock: Lock,
  pencil: Pencil,
  rocket: Rocket,
  search: Search,
  settings: Settings,
  sparkles: Sparkles,
  star: Star,
  terminal: Terminal,
  "thumbs-down": ThumbsDown,
  "thumbs-up": ThumbsUp,
  "trending-down": TrendingDown,
  "trending-up": TrendingUp,
  wand: Wand,
  wrench: Wrench,
  zap: Zap,
};

/** `note:"icon:trending-up"` → the component, or null when unknown/absent. */
export function lucideIcon(name: string | undefined | null): LucideIcon | null {
  if (!name) return null;
  const key = String(name).trim().toLowerCase().replace(/[_\s]+/g, "-");
  return ICONS[key] ?? null;
}

/** Pulls the icon name out of an overlay `note` (`icon:<name>`). */
export function iconNameFromNote(note: string | undefined | null): string | null {
  const m = String(note || "").match(/icon:([a-z0-9-]+)/i);
  return m ? m[1] : null;
}
