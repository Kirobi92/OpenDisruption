'use client';

import axios from 'axios';
import { usePathname, useRouter } from 'next/navigation';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type AuthUser = {
  id: string;
  username: string;
  displayName: string;
  role: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
};

const TOKEN_KEY = 'kirobi.portal.token';
const USER_KEY = 'kirobi.portal.user';

const KNOWN_USERS: Record<string, Pick<AuthUser, 'displayName' | 'role'>> = {
  sven: { displayName: 'Sven', role: 'owner' },
  samira: { displayName: 'Samira', role: 'family' },
  sineo: { displayName: 'Sineo', role: 'creator' },
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function safeParseUser(value: string | null): AuthUser | null {
  if (!value) {
    return null;
  }

  try {
    const parsed = JSON.parse(value) as Partial<AuthUser>;

    if (!parsed.username) {
      return null;
    }

    return {
      id: String(parsed.id ?? parsed.username),
      username: String(parsed.username),
      displayName: String(parsed.displayName ?? parsed.username),
      role: String(parsed.role ?? 'user'),
    };
  } catch {
    return null;
  }
}

function fallbackUser(username: string): AuthUser {
  const normalized = username.trim().toLowerCase();
  const known = KNOWN_USERS[normalized];

  return {
    id: normalized || username,
    username,
    displayName: known?.displayName ?? username,
    role: known?.role ?? 'user',
  };
}

function normalizeLoginResponse(payload: unknown, username: string) {
  const data = (payload ?? {}) as Record<string, unknown>;
  const token =
    data.token ??
    data.access_token ??
    data.jwt ??
    (typeof data.data === 'object' && data.data !== null
      ? (data.data as Record<string, unknown>).token ??
        (data.data as Record<string, unknown>).access_token
      : null);

  const userCandidate =
    data.user ??
    data.profile ??
    (typeof data.data === 'object' && data.data !== null
      ? (data.data as Record<string, unknown>).user
      : null);

  if (!token || typeof token !== 'string') {
    throw new Error('Kein gültiges Token erhalten.');
  }

  if (!userCandidate || typeof userCandidate !== 'object') {
    return { token, user: fallbackUser(username) };
  }

  const userData = userCandidate as Record<string, unknown>;
  const fallback = fallbackUser(username);

  return {
    token,
    user: {
      id: String(userData.id ?? userData.user_id ?? fallback.id),
      username: String(userData.username ?? fallback.username),
      displayName: String(userData.displayName ?? userData.display_name ?? fallback.displayName),
      role: String(userData.role ?? fallback.role),
    },
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const storedToken = window.localStorage.getItem(TOKEN_KEY);
    const storedUser = safeParseUser(window.localStorage.getItem(USER_KEY));

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }

    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      setIsLoading(true);

      try {
        const response = await axios.post(
          `${process.env.NEXT_PUBLIC_BASE_PATH ?? ''}/api/proxy/auth/login`,
          { username, password },
        );
        const normalized = normalizeLoginResponse(response.data, username);

        window.localStorage.setItem(TOKEN_KEY, normalized.token);
        window.localStorage.setItem(USER_KEY, JSON.stringify(normalized.user));

        setToken(normalized.token);
        setUser(normalized.user);
        router.push('/');
      } catch (error) {
        const message =
          axios.isAxiosError(error)
            ? error.response?.data?.detail || error.response?.data?.message || 'Anmeldung fehlgeschlagen.'
            : 'Anmeldung fehlgeschlagen.';
        throw new Error(String(message));
      } finally {
        setIsLoading(false);
      }
    },
    [router],
  );

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
    router.replace('/login');
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, login, logout, isLoading }),
    [isLoading, login, logout, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth muss innerhalb des AuthProvider verwendet werden.');
  }

  return context;
}

export function useRequireAuth() {
  const auth = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (auth.isLoading) {
      return;
    }

    if (!auth.token && pathname !== '/login') {
      router.replace('/login');
    }
  }, [auth.isLoading, auth.token, pathname, router]);

  return {
    ...auth,
    isAuthenticated: Boolean(auth.token),
  };
}
