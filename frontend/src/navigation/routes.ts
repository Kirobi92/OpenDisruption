import { lazy, LazyExoticComponent } from 'react'
import { TabId } from './BottomNav'

type ModuleComponent = LazyExoticComponent<() => JSX.Element>

export const ROUTES: Record<TabId, { title: string; Component: ModuleComponent }> = {
  chat: {
    title: 'Chat',
    Component: lazy(() => import('../modules/chat/ChatModule')),
  },
  agents: {
    title: 'Agenten',
    Component: lazy(() => import('../modules/agents/AgentsModule')),
  },
  creative: {
    title: 'Kreativ',
    Component: lazy(() => import('../modules/creative/CreativeModule')),
  },
  inventory: {
    title: 'Inventar',
    Component: lazy(() => import('../modules/inventory/InventoryModule')),
  },
  family: {
    title: 'Familie',
    Component: lazy(() => import('../modules/family/FamilyModule')),
  },
  system: {
    title: 'System',
    Component: lazy(() => import('../modules/system/SystemModule')),
  },
}
