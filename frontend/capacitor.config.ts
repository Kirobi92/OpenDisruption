import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'de.opendirsruption.kirobi',
  appName: 'Kirobi',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
  android: {
    // Release-Build: signiertes APK via GitHub Actions CI
    // Keystore-Config erfolgt über CI-Secrets (ANDROID_KEYSTORE_*)
    buildOptions: {
      releaseType: 'APK',
    },
  },
  plugins: {
    // Kein LiveReload in Production — nur lokal via CAPACITOR_BUILD env
  },
};

export default config;
