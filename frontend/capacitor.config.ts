import { type CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'de.opendisruption.kirobi',
  appName: 'Kirobi',
  webDir: 'dist',
  // KEIN server.url → Assets werden lokal aus dem APK geladen (bundled)
  android: {
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: true,
  },
};

export default config;
