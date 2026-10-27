// Minimal offline i18n: English + Kannada static labels, plus a demo phrase map
// so the Copilot can accept a Kannada query and map it to an English intent.
// In production this is replaced by Catalyst Zia Services (STT/TTS/translate).

export type Lang = "en" | "kn";

export const LABELS: Record<string, { en: string; kn: string }> = {
  appName: { en: "TRINETRA", kn: "ತ್ರಿನೇತ್ರ" },
  tagline: {
    en: "KSP Crime Intelligence - one engine, two faces",
    kn: "ಕೆಎಸ್‌ಪಿ ಅಪರಾಧ ಗುಪ್ತಚರ - ಒಂದು ಎಂಜಿನ್, ಎರಡು ಮುಖಗಳು",
  },
  copilot: { en: "Copilot", kn: "ಸಹಾಯಕ" },
  warRoom: { en: "War Room", kn: "ವಾರ್ ರೂಮ್" },
  audit: { en: "Audit Log", kn: "ಲೆಕ್ಕಪರಿಶೋಧನೆ" },
  login: { en: "Sign in", kn: "ಸೈನ್ ಇನ್" },
  ask: { en: "Ask", kn: "ಕೇಳಿ" },
  askPlaceholder: {
    en: "Ask about crime data, e.g. chain snatching hotspots last month",
    kn: "ಅಪರಾಧ ಡೇಟಾ ಬಗ್ಗೆ ಕೇಳಿ, ಉದಾ. ಕಳೆದ ತಿಂಗಳು ಚೈನ್ ಕಳ್ಳತನ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು",
  },
  downloadBrief: { en: "Download PDF brief", kn: "ಪಿಡಿಎಫ್ ವರದಿ ಡೌನ್‌ಲೋಡ್" },
  voice: { en: "Voice", kn: "ಧ್ವನಿ" },
  citedFirs: { en: "Cited FIRs", kn: "ಉಲ್ಲೇಖಿತ ಎಫ್‌ಐಆರ್" },
  sqlRun: { en: "SQL executed", kn: "ಚಲಾಯಿಸಿದ SQL" },
  confidence: { en: "Confidence", kn: "ವಿಶ್ವಾಸ" },
};

// Kannada (or romanized) phrase -> canonical English query for the demo.
export const KANNADA_PHRASES: { match: string[]; en: string }[] = [
  {
    match: ["ಚೈನ್ ಕಳ್ಳತನ", "chain kalla", "snatching hotspot"],
    en: "chain snatching hotspots last month",
  },
  {
    match: ["ವಾಹನ ಕಳ್ಳತನ", "vehicle kalla", "bike theft"],
    en: "vehicle theft trend",
  },
];

export function t(key: string, lang: Lang): string {
  return LABELS[key]?.[lang] ?? key;
}

export function mapKannada(input: string): string {
  const lower = input.toLowerCase();
  for (const p of KANNADA_PHRASES) {
    if (p.match.some((m) => input.includes(m) || lower.includes(m.toLowerCase()))) {
      return p.en;
    }
  }
  return input;
}
