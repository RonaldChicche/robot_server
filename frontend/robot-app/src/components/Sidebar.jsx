import { Button } from "@/components/ui/button"
import { BookText, Settings, Info, Atom } from "lucide-react"

const tabs = [
  { key: "table", label: "Tabla", icon: BookText },
  { key: "form", label: "Formulario", icon: Settings },
  { key: "about", label: "Acerca de", icon: Info },
]

export default function Sidebar({ onSelect, active }) {
  return (
    <aside className="w-60 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-2">
      <div className="flex items-center gap-2 mb-6">
        <Atom className="text-cyan-400" size={24} />
        <h2 className="text-lg font-bold tracking-wide">BORUNTE UI</h2>
      </div>

      {tabs.map(({ key, label, icon: Icon }) => (
        <Button
          key={key}
          variant={active === key ? "secondary" : "ghost"}
          onClick={() => onSelect(key)}
          className={`justify-start gap-2 ${active === key ? "border border-cyan-400" : ""}`}
        >
          <Icon size={18} />
          {label}
        </Button>
      ))}
    </aside>
  )
}
