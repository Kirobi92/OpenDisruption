import './BottomNav.css'

export type TabId = 'chat' | 'agents' | 'creative' | 'inventory' | 'family' | 'system'

export interface NavItem {
  id: TabId
  label: string
  icon: string
}

const NAV_ITEMS: NavItem[] = [
  { id: 'chat', label: 'Chat', icon: '◆' },
  { id: 'agents', label: 'Agenten', icon: '🤖' },
  { id: 'creative', label: 'Kreativ', icon: '✦' },
  { id: 'inventory', label: 'Inventar', icon: '▣' },
  { id: 'family', label: 'Familie', icon: '♡' },
  { id: 'system', label: 'System', icon: '⚙' },
]

interface BottomNavProps {
  activeTab: TabId
  onChange: (tab: TabId) => void
}

export function BottomNav({ activeTab, onChange }: BottomNavProps) {
  return (
    <nav className="bottomNav" aria-label="Kirobi Module">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`bottomNavItem ${activeTab === item.id ? 'active' : ''}`}
          onClick={() => onChange(item.id)}
          aria-current={activeTab === item.id ? 'page' : undefined}
        >
          <span className="bottomNavIcon" aria-hidden="true">{item.icon}</span>
          <span className="bottomNavLabel">{item.label}</span>
        </button>
      ))}
    </nav>
  )
}
