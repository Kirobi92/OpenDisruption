import { Suspense, lazy, useState } from 'react'
import { BottomNav, type TabId } from './navigation/BottomNav'
import { ROUTES } from './navigation/routes'
import { StoryIndex } from './stories/StoryIndex'
import './App.css'
import './navigation/BottomNav.css'

// Dev-Story routes — lazy loaded, only active in dev
// /#/story → StoryIndex (handled separately below)
const STORY_ROUTES: Record<string, React.LazyExoticComponent<() => JSX.Element>> = {
  '/story/music-health-config': lazy(() =>
    import('./stories/StoryMusicHealthConfig').then((m) => ({ default: m.StoryMusicHealthConfig as () => JSX.Element }))
  ),
  '/story/system-module': lazy(() =>
    import('./stories/StorySystemModule').then((m) => ({ default: m.StorySystemModule as () => JSX.Element }))
  ),
}

function getHashPath() {
  return window.location.hash.replace(/^#/, '') || '/'
}

export default function App() {
  const [hashPath, setHashPath] = useState(getHashPath)
  const [activeTab, setActiveTab] = useState<TabId>('chat')

  // Listen to hash changes for story navigation
  if (typeof window !== 'undefined') {
    window.onhashchange = () => setHashPath(getHashPath())
  }

  // Story mode: hash-based routing
  // /#/story → Story Index
  if (hashPath === '/story') {
    return <StoryIndex />
  }
  const StoryComponent = STORY_ROUTES[hashPath]
  if (StoryComponent) {
    return (
      <Suspense fallback={<div style={{ padding: 24, color: '#7986cb', fontFamily: 'monospace' }}>Story lädt…</div>}>
        <StoryComponent />
      </Suspense>
    )
  }

  const ActiveModule = ROUTES[activeTab].Component

  return (
    <div className="app shellApp">
      <div className="moduleViewport">
        <Suspense fallback={<div className="moduleLoading">KIROBI lädt {ROUTES[activeTab].title}...</div>}>
          <ActiveModule />
        </Suspense>
      </div>
      <BottomNav activeTab={activeTab} onChange={setActiveTab} />
    </div>
  )
}
