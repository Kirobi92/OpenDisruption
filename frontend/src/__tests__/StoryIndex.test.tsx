/**
 * Unit-Tests: StoryIndex
 * Vitest + @testing-library/react
 *
 * Testszenarien:
 *   1. StoryIndex rendert ohne Crash
 *   2. Alle STORY_ROUTES_META Einträge erscheinen als Links
 *   3. Links haben korrekte href (#/story/...) basierend auf STORY_ROUTES_META
 *   4. Story-Count Badge zeigt korrekte Anzahl
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StoryIndex, STORY_ROUTES_META } from '../stories/StoryIndex'

describe('StoryIndex', () => {
  it('rendert ohne Crash', () => {
    const { container } = render(<StoryIndex />)
    expect(container).toBeTruthy()
  })

  it('zeigt alle STORY_ROUTES_META Einträge als Links', () => {
    render(<StoryIndex />)

    for (const story of STORY_ROUTES_META) {
      // Label sichtbar
      const label = screen.getByText(story.label)
      expect(label).toBeTruthy()
    }
  })

  it('Links haben korrektes href-Attribut basierend auf STORY_ROUTES_META', () => {
    render(<StoryIndex />)

    const links = document.querySelectorAll('a[href]')
    const hrefs = Array.from(links).map((l) => (l as HTMLAnchorElement).getAttribute('href'))

    for (const story of STORY_ROUTES_META) {
      const expectedHref = `#${story.path}`
      expect(hrefs).toContain(expectedHref)
    }
  })

  it('Story-Count Badge zeigt korrekte Anzahl', () => {
    render(<StoryIndex />)

    const count = STORY_ROUTES_META.length
    const countText = count === 1 ? '1 Story verfügbar' : `${count} Stories verfügbar`
    expect(screen.getByText(countText)).toBeTruthy()
  })

  it('Story-Beschreibung ist sichtbar wenn vorhanden', () => {
    render(<StoryIndex />)

    for (const story of STORY_ROUTES_META) {
      if (story.description) {
        // Beschreibung muss irgendwo im Dokument erscheinen
        expect(document.body.textContent).toContain(story.description.slice(0, 20))
      }
    }
  })
})
