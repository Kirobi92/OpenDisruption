import './ModuleCard.css'

interface ModuleCardProps {
  title: string
  subtitle: string
  primaryAction?: { label: string; href: string }
  items?: string[]
}

export function ModuleCard({ title, subtitle, primaryAction, items = [] }: ModuleCardProps) {
  return (
    <section className="moduleCard">
      <div className="moduleCardHeader">
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
      {items.length > 0 && (
        <ul className="moduleCardList">
          {items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      )}
      {primaryAction && (
        <a className="moduleCardAction" href={primaryAction.href} target="_blank" rel="noreferrer">
          {primaryAction.label}
        </a>
      )}
    </section>
  )
}
