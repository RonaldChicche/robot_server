import { useState } from "react"
import { cn } from "@/lib/utils" 
import { BookText, Settings, Info, Atom, Gamepad2, ChevronLeft, ChevronRight, Layers } from "lucide-react"
import { Button } from "@/components/ui/button"

const tabs = [
  { key: "table", label: "Tabla", icon: BookText },
  { key: "form", label: "Formulario", icon: Settings },
  { key: "controller", label: "Controlador", icon: Gamepad2 },
  { key: "process", label: "Proceso", icon: Layers },
  { key: "about", label: "Acerca de", icon: Info },
]

export default function Sidebar({ onSelect, active }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside className={`h-screen bg-slate-900 border-r border-slate-800 p-4 flex flex-col justify-between transition-all duration-300 ${collapsed ? "w-20" : "w-60"}`}>
      <div>
        <div className={`flex items-center gap-2 mb-6 ${collapsed ? "justify-center" : "justify-start"}`}>
          <Atom className="text-cyan-400" size={24} />
          {!collapsed && <h2 className="text-lg font-bold tracking-wide">BORUNTE UI</h2>}
        </div>

        {tabs.map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={active === key ? "secondary" : "ghost"}
            onClick={() => onSelect(key)}
            className={cn(
              "w-full gap-2",
              collapsed ? "justify-center px-0" : "justify-start px-4",
              active === key && "border border-cyan-400"
            )}
          >
            {Icon && <Icon size={18} />}
            {!collapsed && label}
          </Button>
        ))}
      </div>

      <div className="flex justify-end">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="mt-4"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </Button>
      </div>
    </aside>
  )
}
