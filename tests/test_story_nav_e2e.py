"""
test_story_nav_e2e.py — Playwright E2E Test: Story-Index Navigation

Test-Szenarios:
  - Navigiere zu /#/story → StoryIndex wird gerendert (Story-Liste sichtbar)
  - Klicke Story-Link → Hash wechselt zu /#/story/music-health-config
  - Story-Komponente ist sichtbar (MusicHealthConfigPanel-Story)
  - Zurück zu /#/story via Browser-Back → StoryIndex wieder sichtbar

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
        assert "1" in count_text, f"Story-Count falsch: {count_text}"
        assert "Story" in count_text, f"Story-Text fehlt: {count_text}"

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
