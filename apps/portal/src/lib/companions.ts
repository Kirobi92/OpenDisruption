export type CompanionProfile = {
  key: string;
  displayName: string;
  assistantName: string;
  defaultAgent: string;
  hermesService: string;
  hermesPath: string;
  userFolder: string;
  hermesDataPath: string;
  headline: string;
  summary: string;
  focus: string;
};

const DEFAULT_PROFILE: CompanionProfile = {
  key: 'kirobi',
  displayName: 'Kirobi',
  assistantName: 'Hermes Core',
  defaultAgent: 'kirobi',
  hermesService: 'hermes-runtime',
  hermesPath: '/hermes/',
  userFolder: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Sven',
  hermesDataPath: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Sven/agent/hermes-runtime',
  headline: 'Dein lokaler Hermes-Begleiter ist bereit.',
  summary: 'Chat, Voice, Uploads und Wissensarbeit laufen ueber dieselbe lokale Benutzeroberflaeche.',
  focus: 'Alltag, Wissen, Kreativarbeit und persoenliche Entwicklung.',
};

const PROFILES: Record<string, CompanionProfile> = {
  sven: {
    key: 'sven',
    displayName: 'Sven',
    assistantName: 'Hermes Sven',
    defaultAgent: 'sven',
    hermesService: 'hermes-runtime',
    hermesPath: '/hermes/',
    userFolder: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Sven',
    hermesDataPath: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Sven/agent/hermes-runtime',
    headline: 'Hermes Sven orchestriert OpenDisruption lokal auf deiner Hardware.',
    summary: 'Operator-, Telegram-, Coding- und Wissens-Orchestrierung bleiben in deinem persoenlichen lokalen Stack.',
    focus: 'Strategie, Produktaufbau, Daily Orchestration und technische Steuerung.',
  },
  samira: {
    key: 'samira',
    displayName: 'Samira',
    assistantName: 'Hermes Samira',
    defaultAgent: 'samira',
    hermesService: 'hermes-samira-runtime',
    hermesPath: '/hermes-samira/',
    userFolder: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Samira',
    hermesDataPath: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Samira/agent/hermes-runtime',
    headline: 'Hermes Samira begleitet dich sanft, klar und mit eigenem Kontext.',
    summary: 'Familienkontext, Onboarding, Reflexion und persoenliche Unterstuetzung bleiben getrennt und lokal.',
    focus: 'Familie, Selbstreflexion, Routinen und geschuetzte persoenliche Begleitung.',
  },
  sineo: {
    key: 'sineo',
    displayName: 'Sineo',
    assistantName: 'Hermes Sineo',
    defaultAgent: 'sineo',
    hermesService: 'hermes-sineo-runtime',
    hermesPath: '/hermes-sineo/',
    userFolder: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Sineo',
    hermesDataPath: '/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/Sineo/agent/hermes-runtime',
    headline: 'Hermes Sineo ist auf Creator-, Lern- und Gaming-Flow ausgerichtet.',
    summary: 'Kreative Ideen, Medienproduktion, Uploads und persoenliche Wissensarbeit laufen ueber deine eigene Instanz.',
    focus: 'Kreativitaet, Projekte, Medien, Lernen und Momentum.',
  },
};

function normalizeUsername(username?: string | null): string {
  return username?.trim().toLowerCase() ?? '';
}

export function resolveCompanionProfile(username?: string | null): CompanionProfile {
  return PROFILES[normalizeUsername(username)] ?? DEFAULT_PROFILE;
}

export function resolveDefaultAgent(username?: string | null): string {
  return resolveCompanionProfile(username).defaultAgent;
}
