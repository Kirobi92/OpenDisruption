"""
test_story_nav_e2e.py — Playwright E2E Test: Story-Index Navigation

Test-Szenarios:
  - Navigiere zu /#/story → StoryIndex wird gerendert (Story-Liste sichtbar)
  - Klicke Story-Link → Hash wechselt zu /#/story/music-health-config
  - Story-Komponente ist sichtbar (MusicHealthConfigPanel-Story)
  - Zurück zu /#/story via Browser-Back → StoryIndex wieder sichtbar
  - ScAlertsPanel: Keyboard-Navigation ArrowRight (Page 1→2) + ArrowLeft (Page 2→1)
  - ScAlertsPanel: Seitenindikator-Update nach Tastatur-Navigation

Approach: Minimaler Inline-HTML-Mock simuliert das Hash-Routing von App.tsx
(STORY_ROUTES + StoryIndex analog zu App.tsx + StoryIndex.tsx),
sodass kein laufender Dev-Server benötigt wird.
"""

import pytest
from playwright.sync_api import Page


# ──────────────────────────────────────────────────────────────────────────────
# Inline-HTML simuliert App.tsx Hash-Routing + StoryIndex + Story-Route
# ──────────────────────────────────────────────────────────────────────────────
STORY_NAV_HTML = r"""
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Kirobi Story-Nav E2E</title>
  <style>
    body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; margin: 0; padding: 0; }
    .story-index { padding: 24px 16px; max-width: 640px; margin: 0 auto; }
    .story-link {
      display: block; padding: 14px 16px; background: #16213e;
      border: 1px solid #2a2a4a; border-radius: 8px;
      text-decoration: none; color: inherit; margin-bottom: 12px;
    }
    .story-label { color: #7986cb; font-size: 13px; font-weight: 700; }
    .story-badge {
      background: #0f3460; color: #7986cb; font-size: 10px;
      padding: 1px 6px; border-radius: 4px; margin-left: 8px;
    }
    .story-desc { color: #aaa; font-size: 12px; margin-top: 4px; }
    .story-path { color: #555; font-size: 11px; margin-top: 6px; }
    .story-count { color: #888; font-size: 12px; margin-top: 6px; }
    .story-panel { padding: 24px; }
    .music-health-panel {
      background: #16213e; border: 1px solid #2a2a4a;
      border-radius: 8px; padding: 16px; margin-top: 16px;
    }
    .refresh-value { color: #7986cb; font-size: 20px; font-weight: 700; }
    .back-link { color: #7986cb; font-size: 12px; display: inline-block; margin-bottom: 16px; }
    /* ScAlertsPanel Styles */
    .sc-alerts-container { background: #16213e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px; margin-top: 16px; }
    .sc-alerts-header { display: flex; justify-content: space-between; font-size: 13px; color: #7986cb; margin-bottom: 8px; }
    .sc-alerts-total { color: #555; font-size: 11px; }
    .sc-alerts-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .sc-nav-hint { color: #555; font-size: 10px; }
    .sc-page-indicator { color: #7986cb; font-size: 13px; font-weight: 700; }
    .sc-alerts-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .sc-alerts-table th { text-align: left; color: #7986cb; font-size: 10px; text-transform: uppercase; padding: 8px 6px; border-bottom: 1px solid #2a2a4a; }
    .sc-alerts-table td { padding: 8px 6px; border-bottom: 1px solid #1a1a3e; color: #ccc; }
    .sc-td-run code { color: #7986cb; font-size: 11px; }
    .sc-td-delta.delta-up { color: #4caf50; }
    .sc-td-delta.delta-down { color: #f44336; }
    .sc-td-delta.delta-neutral { color: #888; }
    .sc-alerts-pagination { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 16px; padding-top: 12px; border-top: 1px solid #2a2a4a; }
    .sc-page-btn { background: #0f3460; color: #7986cb; border: 1px solid #2a2a4a; border-radius: 4px; padding: 6px 14px; cursor: pointer; font-size: 12px; }
    .sc-page-btn:disabled { opacity: 0.4; cursor: default; }
    .sc-page-dots { color: #7986cb; font-size: 12px; }
    #root { min-height: 100vh; }
  </style>
</head>
<body>
<div id="root"></div>

<script>
// STORY_ROUTES_META analog zu StoryIndex.tsx
const STORY_ROUTES_META = [
  {
    path: '/story/music-health-config',
    label: 'MusicHealthConfigPanel',
    description: 'GET/PUT /api/music-health-config — Refresh-Intervall anzeigen & editieren (3 Szenarien: Default/ENV/Runtime)',
  },
  {
    path: '/story/sc-alerts-panel',
    label: 'ScAlertsPanel',
    description: '/api/sc-alerts — SC-Alert-Events mit Pagination (10 pro Seite) & Keyboard-Navigation (ArrowRight/ArrowLeft)',
  }
];

// Analog zu StoryMusicHealthConfig.tsx — minimal Mock
function renderMusicHealthConfigStory() {
  return `
    <div class="story-panel">
      <a href="#/story" class="back-link" id="back-to-index">← Story Index</a>
      <h2 style="color:#7986cb;font-size:14px;letter-spacing:2px;text-transform:uppercase;">
        Dev Story: MusicHealthConfigPanel
      </h2>
      <div class="music-health-panel" data-testid="music-health-config-panel">
        <div style="font-size:11px;color:#888;margin-bottom:8px;">
          ⚙️ Music Health Refresh Config
        </div>
        <div>
          Interval: <span class="refresh-value" id="refresh-value">30</span>s
        </div>
        <div style="font-size:11px;color:#666;margin-top:4px;">
          Source: <span id="config-source">default</span>
        </div>
        <button id="edit-btn" style="margin-top:12px;background:#0f3460;color:#7986cb;border:1px solid #2a2a4a;border-radius:4px;padding:6px 14px;cursor:pointer;">
          ✏️ Bearbeiten
        </button>
      </div>
      <div style="font-size:11px;color:#555;margin-top:20px;">
        Route: #/story/music-health-config
      </div>
    </div>
  `;
}

// Analog zu ScAlertsPanel.tsx — Mock mit Pagination (10 pro Seite) & Keyboard-Navigation
const SC_ALERTS_MOCK = [
  { run_id: 26250297372, sc_issue_count: 1, delta: 1, timestamp: '2026-05-21T20:43:46Z' },
  { run_id: 26249901647, sc_issue_count: 1, delta: 1, timestamp: '2026-05-21T20:43:48Z' },
  { run_id: 26248000123, sc_issue_count: 3, delta: 2, timestamp: '2026-05-21T18:20:11Z' },
  { run_id: 26246000987, sc_issue_count: 0, delta: 0, timestamp: '2026-05-21T16:45:33Z' },
  { run_id: 26244000555, sc_issue_count: 5, delta: 3, timestamp: '2026-05-21T14:10:07Z' },
  { run_id: 26242000111, sc_issue_count: 2, delta: -1, timestamp: '2026-05-21T12:30:00Z' },
  { run_id: 26240000888, sc_issue_count: 1, delta: 0, timestamp: '2026-05-21T10:15:42Z' },
  { run_id: 26238000444, sc_issue_count: 4, delta: 2, timestamp: '2026-05-21T08:00:19Z' },
  { run_id: 26236000222, sc_issue_count: 0, delta: 0, timestamp: '2026-05-21T06:30:55Z' },
  { run_id: 26234000999, sc_issue_count: 2, delta: 1, timestamp: '2026-05-21T04:10:28Z' },
  { run_id: 26232000777, sc_issue_count: 1, delta: 0, timestamp: '2026-05-21T02:45:17Z' },
  { run_id: 26230000555, sc_issue_count: 6, delta: 4, timestamp: '2026-05-21T00:20:03Z' },
  { run_id: 26228000333, sc_issue_count: 0, delta: -2, timestamp: '2026-05-20T22:10:44Z' },
  { run_id: 26226000111, sc_issue_count: 3, delta: 1, timestamp: '2026-05-20T20:00:12Z' },
  { run_id: 26224000888, sc_issue_count: 1, delta: -1, timestamp: '2026-05-20T18:30:00Z' },
];
const SC_ALERTS_PER_PAGE = 10;

let scCurrentPage = 1;
let scTotalPages = Math.ceil(SC_ALERTS_MOCK.length / SC_ALERTS_PER_PAGE);

function renderScAlertRow(alert) {
  const deltaClass = alert.delta > 0 ? 'delta-up' : alert.delta < 0 ? 'delta-down' : 'delta-neutral';
  const deltaSign = alert.delta > 0 ? '+' : '';
  return `
    <tr class="sc-alert-row">
      <td class="sc-td-run"><code>${alert.run_id}</code></td>
      <td class="sc-td-count">${alert.sc_issue_count}</td>
      <td class="sc-td-delta ${deltaClass}">${deltaSign}${alert.delta}</td>
      <td class="sc-td-time">${alert.timestamp.replace('T', ' ').replace('Z', '')}</td>
    </tr>`;
}

function renderScAlertsPanelStory() {
  const start = (scCurrentPage - 1) * SC_ALERTS_PER_PAGE;
  const pageAlerts = SC_ALERTS_MOCK.slice(start, start + SC_ALERTS_PER_PAGE);
  const rows = pageAlerts.map(renderScAlertRow).join('');

  return `
    <div class="story-panel" id="sc-alerts-panel">
      <a href="#/story" class="back-link" id="back-to-index">← Story Index</a>
      <h2 style="color:#7986cb;font-size:14px;letter-spacing:2px;text-transform:uppercase;">
        Dev Story: ScAlertsPanel
      </h2>
      <div class="sc-alerts-container" data-testid="sc-alerts-panel">
        <div class="sc-alerts-header">
          <span>🔍 SC Alert Events</span>
          <span class="sc-alerts-total">${SC_ALERTS_MOCK.length} total</span>
        </div>
        <div class="sc-alerts-nav">
          <span class="sc-nav-hint" id="sc-nav-hint">← → Tastatur-Navigation</span>
          <span class="sc-page-indicator" id="sc-page-indicator" data-testid="sc-page-indicator">
            Seite ${scCurrentPage} / ${scTotalPages}
          </span>
        </div>
        <table class="sc-alerts-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Issues</th>
              <th>Δ</th>
              <th>Zeitstempel</th>
            </tr>
          </thead>
          <tbody id="sc-alerts-tbody">
            ${rows}
          </tbody>
        </table>
        <div class="sc-alerts-pagination">
          <button class="sc-page-btn" id="sc-prev-btn" ${scCurrentPage === 1 ? 'disabled' : ''}
            onclick="scGoToPage(scCurrentPage - 1)">← Zurück</button>
          <span class="sc-page-dots" id="sc-page-dots">${scCurrentPage} / ${scTotalPages}</span>
          <button class="sc-page-btn" id="sc-next-btn" ${scCurrentPage === scTotalPages ? 'disabled' : ''}
            onclick="scGoToPage(scCurrentPage + 1)">Weiter →</button>
        </div>
      </div>
      <div style="font-size:11px;color:#555;margin-top:20px;">
        Route: #/story/sc-alerts-panel
      </div>
    </div>
  `;
}

function scGoToPage(page) {
  if (page < 1 || page > scTotalPages) return;
  scCurrentPage = page;
  document.getElementById('root').innerHTML = renderScAlertsPanelStory();
  // Re-register keyboard listener nach DOM-Update
  document.addEventListener('keydown', scKeyHandler);
}

function scKeyHandler(e) {
  if (e.key === 'ArrowRight' && scCurrentPage < scTotalPages) {
    e.preventDefault();
    scGoToPage(scCurrentPage + 1);
  } else if (e.key === 'ArrowLeft' && scCurrentPage > 1) {
    e.preventDefault();
    scGoToPage(scCurrentPage - 1);
  }
}

// Analog zu StoryIndex.tsx
function renderStoryIndex() {
  const links = STORY_ROUTES_META.map(story => `
    <a href="#${story.path}" class="story-link" data-path="${story.path}">
      <div>
        <span class="story-label">${story.label}</span>
        <span class="story-badge">STORY</span>
      </div>
      <div class="story-desc">${story.description || ''}</div>
      <div class="story-path">#${story.path}</div>
    </a>
  `).join('');

  return `
    <div class="story-index" id="story-index">
      <div style="color:#7986cb;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">
        Kirobi Dev-Stories
      </div>
      <h1 style="margin:0;font-size:22px;color:#fff;font-weight:700;">📖 Story Index</h1>
      <div class="story-count" id="story-count">
        ${STORY_ROUTES_META.length} ${STORY_ROUTES_META.length === 1 ? 'Story' : 'Stories'} verfügbar
      </div>
      <div style="margin-top:24px;" id="story-list">
        ${links}
      </div>
      <div style="margin-top:40px;border-top:1px solid #2a2a4a;color:#444;font-size:11px;padding-top:12px;text-align:center;">
        Neue Stories in STORY_ROUTES_META eintragen
      </div>
    </div>
  `;
}

// App.tsx Hash-Routing Simulation
function getHashPath() {
  return window.location.hash.replace(/^#/, '') || '/';
}

function render() {
  const root = document.getElementById('root');
  const path = getHashPath();

  if (path === '/story') {
    root.innerHTML = renderStoryIndex();
  } else if (path === '/story/music-health-config') {
    root.innerHTML = renderMusicHealthConfigStory();
  } else if (path === '/story/sc-alerts-panel') {
    root.innerHTML = renderScAlertsPanelStory();
    // Keyboard-Navigation registrieren
    document.addEventListener('keydown', scKeyHandler);
  } else {
    // Default: App-Shell
    root.innerHTML = `
      <div style="padding:24px;color:#7986cb;font-family:monospace;">
        <div>Kirobi App Shell — <a href="#/story" style="color:#7986cb;">📖 Stories</a></div>
      </div>
    `;
  }
}

// Initial render + hash-change listener
render();
window.addEventListener('hashchange', render);
</script>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def story_html_file(tmp_path_factory):
    """Schreibt STORY_NAV_HTML als temporäre Datei."""
    d = tmp_path_factory.mktemp("story_nav_e2e")
    f = d / "story_nav.html"
    f.write_text(STORY_NAV_HTML, encoding="utf-8")
    return str(f)


@pytest.fixture(scope="session")
def story_base_url(story_html_file):
    """file:// URL der Story-Nav-Seite."""
    return f"file://{story_html_file}"


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestStoryIndexNavE2E:
    """E2E Navigation-Tests für Story-Index (/#/story)."""

    def test_story_index_erreichbar(self, page: Page, story_base_url: str):
        """
        Navigiere zu /#/story → StoryIndex wird gerendert.
        Story-Liste und Headline sichtbar.
        """
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-index", timeout=3000)

        # Headline sichtbar
        assert page.is_visible("#story-index"), "StoryIndex nicht sichtbar"

        # Story-Count Badge
        count_text = page.locator("#story-count").inner_text()
        assert "2" in count_text, f"Story-Count falsch: {count_text}"
        assert "Stories" in count_text, f"Stories-Text fehlt: {count_text}"

    def test_story_link_vorhanden(self, page: Page, story_base_url: str):
        """StoryIndex zeigt Link für MusicHealthConfigPanel Story."""
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-list", timeout=3000)

        link = page.locator("[data-path='/story/music-health-config']")
        assert link.is_visible(), "Story-Link für MusicHealthConfigPanel nicht sichtbar"

        # Label korrekt
        label = link.locator(".story-label").inner_text()
        assert "MusicHealthConfigPanel" in label, f"Falsches Label: {label}"

    def test_story_link_klick_navigiert(self, page: Page, story_base_url: str):
        """
        Klick auf Story-Link → Hash wechselt zu /#/story/music-health-config
        → Story-Komponente wird sichtbar.
        """
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-list", timeout=3000)

        # Klick auf Story-Link
        page.locator("[data-path='/story/music-health-config']").click()
        page.wait_for_timeout(200)

        # Hash muss gewechselt haben
        current_hash = page.evaluate("window.location.hash")
        assert current_hash == "#/story/music-health-config", \
            f"Hash nicht korrekt nach Klick: {current_hash}"

    def test_story_komponente_sichtbar_nach_navigation(self, page: Page, story_base_url: str):
        """
        Nach Klick auf Story-Link ist MusicHealthConfigPanel-Story-Komponente sichtbar.
        Panel mit Refresh-Value und Edit-Button muss vorhanden sein.
        """
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-list", timeout=3000)
        page.locator("[data-path='/story/music-health-config']").click()

        # Story-Panel sichtbar
        page.wait_for_selector("[data-testid='music-health-config-panel']", timeout=3000)
        assert page.is_visible("[data-testid='music-health-config-panel']"), \
            "MusicHealthConfigPanel Story nicht sichtbar"

        # Refresh-Value vorhanden
        refresh_val = page.locator("#refresh-value").inner_text()
        assert refresh_val.isdigit(), f"Kein gültiger Refresh-Wert: {refresh_val}"

        # Edit-Button sichtbar
        assert page.is_visible("#edit-btn"), "Edit-Button nicht sichtbar"

    def test_zurueck_zum_story_index(self, page: Page, story_base_url: str):
        """
        Nach Story-Navigation → Back-Link → StoryIndex wieder sichtbar.
        """
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-list", timeout=3000)
        page.locator("[data-path='/story/music-health-config']").click()
        page.wait_for_selector("[data-testid='music-health-config-panel']", timeout=3000)

        # Back-Link klicken
        page.locator("#back-to-index").click()
        page.wait_for_timeout(200)

        # StoryIndex wieder sichtbar
        page.wait_for_selector("#story-index", timeout=3000)
        assert page.is_visible("#story-index"), "StoryIndex nach Back-Navigation nicht sichtbar"

        # Hash zurück auf /#/story
        current_hash = page.evaluate("window.location.hash")
        assert current_hash == "#/story", f"Hash nicht #/story: {current_hash}"

    def test_direkte_story_url_erreichbar(self, page: Page, story_base_url: str):
        """
        Direkte Navigation zu /#/story/music-health-config (ohne Umweg über Index)
        → Story-Komponente sofort sichtbar (Deep-Link-Support).
        """
        page.goto(f"{story_base_url}#/story/music-health-config")
        page.wait_for_selector("[data-testid='music-health-config-panel']", timeout=3000)
        assert page.is_visible("[data-testid='music-health-config-panel']"), \
            "Deep-Link zu Story-Route fehlgeschlagen"

    def test_story_path_in_link_angezeigt(self, page: Page, story_base_url: str):
        """StoryIndex zeigt Story-Path (#/story/music-health-config) sichtbar an."""
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-list", timeout=3000)

        link = page.locator("[data-path='/story/music-health-config']")
        path_text = link.locator(".story-path").inner_text()
        assert "/story/music-health-config" in path_text, \
            f"Story-Path nicht im Link angezeigt: {path_text}"


class TestScAlertsPanelKeyboardNavE2E:
    """E2E Keyboard-Navigation-Tests für ScAlertsPanel (/#/story/sc-alerts-panel)."""

    def test_sc_alerts_panel_erreichbar(self, page: Page, story_base_url: str):
        """
        Navigiere direkt zu /#/story/sc-alerts-panel → ScAlertsPanel wird gerendert.
        Panel, Tabelle und Seitenindikator sichtbar.
        """
        page.goto(f"{story_base_url}#/story/sc-alerts-panel")
        page.wait_for_selector("[data-testid='sc-alerts-panel']", timeout=3000)

        assert page.is_visible("[data-testid='sc-alerts-panel']"), \
            "ScAlertsPanel nicht sichtbar"

        # Seitenindikator zeigt Seite 1 von 2
        indicator = page.locator("[data-testid='sc-page-indicator']")
        assert indicator.is_visible(), "Seitenindikator nicht sichtbar"
        indicator_text = indicator.inner_text()
        assert "Seite 1" in indicator_text, f"Seitenindikator falsch: {indicator_text}"
        assert "/ 2" in indicator_text, f"Total-Pages fehlt: {indicator_text}"

        # Tabelle mit 10 Zeilen (erste Seite)
        rows = page.locator(".sc-alert-row")
        assert rows.count() == 10, f"Zeilenanzahl Seite 1 falsch: {rows.count()}"

    def test_keyboard_arrow_right_page_1_to_2(self, page: Page, story_base_url: str):
        """
        ArrowRight auf ScAlertsPanel feuert Pagination Page 1 → Page 2.
        Seitenindikator aktualisiert auf „Seite 2 / 2“.
        """
        page.goto(f"{story_base_url}#/story/sc-alerts-panel")
        page.wait_for_selector("[data-testid='sc-alerts-panel']", timeout=3000)

        # Vorher: Seite 1
        indicator = page.locator("[data-testid='sc-page-indicator']")
        assert "Seite 1" in indicator.inner_text(), "Start nicht auf Seite 1"

        # ArrowRight feuern
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)

        # Nachher: Seite 2
        indicator = page.locator("[data-testid='sc-page-indicator']")
        indicator_text = indicator.inner_text()
        assert "Seite 2" in indicator_text, \
            f"ArrowRight hat nicht zu Seite 2 geführt: {indicator_text}"
        assert "/ 2" in indicator_text, "Total-Pages falsch nach Navigation"

        # Nur 5 Zeilen auf Seite 2 (15 total, 10 pro Seite)
        rows = page.locator(".sc-alert-row")
        assert rows.count() == 5, f"Zeilenanzahl Seite 2 falsch: {rows.count()}"

        # Next-Button ist disabled auf letzter Seite
        next_btn = page.locator("#sc-next-btn")
        assert next_btn.is_disabled(), "Next-Button nicht disabled auf letzter Seite"

        # Prev-Button ist enabled
        prev_btn = page.locator("#sc-prev-btn")
        assert prev_btn.is_enabled(), "Prev-Button nicht enabled auf Seite 2"

    def test_keyboard_arrow_left_page_2_to_1(self, page: Page, story_base_url: str):
        """
        Von Page 2 ArrowLeft → zurück zu Page 1.
        Seitenindikator aktualisiert auf „Seite 1 / 2“.
        """
        page.goto(f"{story_base_url}#/story/sc-alerts-panel")
        page.wait_for_selector("[data-testid='sc-alerts-panel']", timeout=3000)

        # Erst zu Seite 2 navigieren
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        assert "Seite 2" in page.locator("[data-testid='sc-page-indicator']").inner_text()

        # ArrowLeft feuern
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(300)

        # Zurück auf Seite 1
        indicator = page.locator("[data-testid='sc-page-indicator']")
        indicator_text = indicator.inner_text()
        assert "Seite 1" in indicator_text, \
            f"ArrowLeft hat nicht zu Seite 1 zurückgeführt: {indicator_text}"

        # Wieder 10 Zeilen
        rows = page.locator(".sc-alert-row")
        assert rows.count() == 10, f"Zeilenanzahl Seite 1 nach Rückkehr falsch: {rows.count()}"

        # Prev-Button ist disabled auf erster Seite
        prev_btn = page.locator("#sc-prev-btn")
        assert prev_btn.is_disabled(), "Prev-Button nicht disabled auf Seite 1"

    def test_keyboard_arrow_right_boundary_no_change(self, page: Page, story_base_url: str):
        """
        ArrowRight auf letzter Seite (Seite 2) ändert nichts —
        Boundary-Check: kein Wrap-Around, Seitenindikator bleibt bei 2.
        """
        page.goto(f"{story_base_url}#/story/sc-alerts-panel")
        page.wait_for_selector("[data-testid='sc-alerts-panel']", timeout=3000)

        # Zu Seite 2
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        assert "Seite 2" in page.locator("[data-testid='sc-page-indicator']").inner_text()

        # Nochmal ArrowRight — sollte auf Seite 2 bleiben
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)

        indicator_text = page.locator("[data-testid='sc-page-indicator']").inner_text()
        assert "Seite 2" in indicator_text, \
            f"ArrowRight auf letzter Seite hat Seite geändert: {indicator_text}"

    def test_keyboard_arrow_left_boundary_no_change(self, page: Page, story_base_url: str):
        """
        ArrowLeft auf erster Seite ändert nichts —
        Boundary-Check: kein Wrap-Around, Seitenindikator bleibt bei 1.
        """
        page.goto(f"{story_base_url}#/story/sc-alerts-panel")
        page.wait_for_selector("[data-testid='sc-alerts-panel']", timeout=3000)

        # Auf Seite 1 ArrowLeft — sollte nichts ändern
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(300)

        indicator_text = page.locator("[data-testid='sc-page-indicator']").inner_text()
        assert "Seite 1" in indicator_text, \
            f"ArrowLeft auf Seite 1 hat Seite geändert: {indicator_text}"

        # Prev-Button weiterhin disabled
        assert page.locator("#sc-prev-btn").is_disabled(), \
            "Prev-Button sollte auf Seite 1 disabled bleiben"

    def test_button_click_navigation(self, page: Page, story_base_url: str):
        """
        Button-Klick (Weiter/Zurück) funktioniert parallel zur Tastatur-Navigation.
        """
        page.goto(f"{story_base_url}#/story/sc-alerts-panel")
        page.wait_for_selector("[data-testid='sc-alerts-panel']", timeout=3000)

        # Weiter-Button klicken
        page.locator("#sc-next-btn").click()
        page.wait_for_timeout(300)
        assert "Seite 2" in page.locator("[data-testid='sc-page-indicator']").inner_text()

        # Zurück-Button klicken
        page.locator("#sc-prev-btn").click()
        page.wait_for_timeout(300)
        assert "Seite 1" in page.locator("[data-testid='sc-page-indicator']").inner_text()

    def test_story_link_vorhanden_sc_alerts(self, page: Page, story_base_url: str):
        """StoryIndex zeigt Link für ScAlertsPanel Story."""
        page.goto(f"{story_base_url}#/story")
        page.wait_for_selector("#story-list", timeout=3000)

        link = page.locator("[data-path='/story/sc-alerts-panel']")
        assert link.is_visible(), "Story-Link für ScAlertsPanel nicht sichtbar"

        label = link.locator(".story-label").inner_text()
        assert "ScAlertsPanel" in label, f"Falsches Label: {label}"
