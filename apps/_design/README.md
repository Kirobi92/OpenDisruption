---
zone: WORKSPACE
created_by: claude-opus-4.7
created_at: 2026-05-09
version: 1.0
---

# Kirobi Design System — Source of Truth

**Zone:** WORKSPACE
**Apps:** `apps/web`, `apps/dashboard`, `apps/voice`
**Sync rule:** When you change `tokens.css` here, you must mirror the change into:

- `apps/web/src/app/globals.css` (token block at top)
- `apps/dashboard/src/app/globals.css` (token block at top)
- `apps/voice/src/app/globals.css` (token block at top)
- `apps/web/tailwind.config.js` (theme.extend)
- `apps/dashboard/tailwind.config.ts` (theme.extend)
- `apps/voice/tailwind.config.ts` (theme.extend)

Reason: Next.js does not let three independent apps share a CSS file across build contexts without a workspace setup. The repo has explicitly chosen NOT to introduce a workspace (see `AGENTS.md`). So we keep three identical copies and treat this file as the spec.

---

## Design Pillars

1. **Deep Space dark theme** with cool undertones (Midnight + Indigo + faint Teal).
2. **Two accent rails:** Cyan (information / flow) and Magenta (action / signal).
3. **Glassmorphism** with multi-layer blur, low opacity surfaces, color-tinted shadows.
4. **Spring-based motion** via framer-motion. All transitions respect `prefers-reduced-motion`.
5. **No 3D / no GSAP** — bundle stays under 30 KB extra (PWA constraint).

---

## Color Tokens

| Token | Value | Usage |
|---|---|---|
| `--bg-void` | `#040614` | Page background, lowest depth |
| `--bg-deep` | `#080b1f` | Surface base |
| `--bg-rise` | `#0d1230` | Cards, raised surfaces |
| `--bg-glass` | `rgba(15, 20, 50, 0.55)` | Frosted glass layer |
| `--border-subtle` | `rgba(255, 255, 255, 0.06)` | Default border |
| `--border-glow` | `rgba(120, 220, 255, 0.18)` | Active / focus ring |
| `--text-primary` | `#f4f6ff` | Main text |
| `--text-secondary` | `#9aa3c7` | Subdued text |
| `--text-muted` | `#5a627e` | Hints, captions |
| `--accent-cyan` | `#5eead4` | Primary accent (flow / info) |
| `--accent-cyan-glow` | `rgba(94, 234, 212, 0.45)` | Glow halo |
| `--accent-magenta` | `#e879f9` | Secondary accent (action / signal) |
| `--accent-magenta-glow` | `rgba(232, 121, 249, 0.4)` | Glow halo |
| `--accent-violet` | `#a78bfa` | Tertiary accent (intelligence) |
| `--accent-gold` | `#fbbf24` | Warmth / warning |

## Tailwind Color Aliases

The `kirobi.*` scale is **unified across all three apps** (was three different scales before — cyan/violet/cyan):

```js
kirobi: {
  50:  '#ecfeff',
  100: '#cffafe',
  200: '#a5f3fc',
  300: '#67e8f9',
  400: '#22d3ee',
  500: '#06b6d4',  // primary
  600: '#0891b2',
  700: '#0e7490',
  800: '#155e75',
  900: '#164e63',
  950: '#083344',
}
```

Plus accent scales `magenta.*` and `violet.*` (Tailwind defaults).

## Motion Tokens

| Token | Value |
|---|---|
| `--ease-spring` | `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out-expo, "spring without overshoot") |
| `--ease-glide` | `cubic-bezier(0.4, 0, 0.2, 1)` |
| `--dur-fast` | `150ms` |
| `--dur-base` | `280ms` |
| `--dur-slow` | `520ms` |

Framer-motion preset: `transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}`.

## Shadow Tokens

| Token | Use |
|---|---|
| `--shadow-glow-cyan` | `0 0 24px var(--accent-cyan-glow), 0 0 48px var(--accent-cyan-glow)` |
| `--shadow-glow-magenta` | `0 0 24px var(--accent-magenta-glow)` |
| `--shadow-card` | `0 1px 0 rgba(255,255,255,0.04) inset, 0 12px 32px -8px rgba(0,0,0,0.6)` |
| `--shadow-float` | `0 24px 48px -12px rgba(6,8,30,0.8), 0 0 0 1px var(--border-subtle) inset` |

## Typography

- Family: Inter (already loaded via `next/font/google` in all apps).
- Display tracking: `-0.02em`.
- Body tracking: `0`.
- Headline weight: 600. Body weight: 400. Captions weight: 500 + uppercase + `tracking-[0.22em]`.

## Accessibility

- Every animation honors `@media (prefers-reduced-motion: reduce)` → motion duration → 0.
- Focus rings: 2px solid `var(--accent-cyan)` with 4px offset.
- Contrast: text-primary on bg-void ≥ 13.5:1 (AAA).
