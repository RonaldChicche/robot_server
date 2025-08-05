import { useState, useEffect } from "react"
import { API_BASE_URL } from "@/config"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Pencil, Trash2 } from "lucide-react"

export default function RecetasView() {
  const [recetas, setRecetas] = useState([])
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState({
    titulo: "",
    long_caja: 0,
    ancho_caja: 0,
    altura_caja: 0,
    long_barra: 0,
    ancho_barra: 0,
    espesor: 0,
    peso: 0,
  })

  const fetchRecetas = () => {
    fetch(`${API_BASE_URL}/api/recetas`)
      .then(res => res.json())
      .then(data => setRecetas(data))
  }

  const handleChange = (key, val) => {
    setForm(prev => ({ ...prev, [key]: key === "titulo" ? val : parseFloat(val) }))
  }

  const resetForm = () => {
    setForm({ titulo: "", long_caja: 0, ancho_caja: 0, altura_caja: 0, long_barra: 0, ancho_barra: 0, espesor: 0, peso: 0 })
    setEditId(null)
  }

  const handleSubmit = () => {
    const method = editId ? "PUT" : "POST"
    const url = editId ? `${API_BASE_URL}/api/recetas/${editId}` : `${API_BASE_URL}/api/recetas`

    fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    }).then(() => {
      fetchRecetas()
      resetForm()
    })
  }

  const handleDelete = (id) => {
    if (!confirm("¿Eliminar receta permanentemente?")) return
    fetch(`${API_BASE_URL}/api/recetas/${id}`, { method: "DELETE" })
      .then(() => fetchRecetas())
  }

  const handleEdit = (receta) => {
    setEditId(receta.id)
    setForm({ ...receta })
  }

  useEffect(() => {
    fetchRecetas()
  }, [])

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold text-white">Gestión de Recetas</h1>

      <div className="bg-slate-800 p-6 rounded-xl space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Object.entries(form).map(([key, value]) => (
            <div key={key}>
              <label className="block text-white font-semibold capitalize">{key.replace("_", " ")}</label>
              <Input
                value={value}
                onChange={(e) => handleChange(key, e.target.value)}
                type={key === "titulo" ? "text" : "number"}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-3">
          <Button className="bg-cyan-600 hover:bg-cyan-700" onClick={handleSubmit}>
            {editId ? "Actualizar Receta" : "Agregar Receta"}
          </Button>
          {editId && (
            <Button variant="ghost" onClick={resetForm}>
              Cancelar
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold text-white">Lista de Recetas</h2>
        {recetas.map((r) => (
          <div key={r.id} className="flex justify-between items-center bg-slate-700 text-white px-4 py-3 rounded">
            <div>
              <strong>{r.titulo}</strong> – Caja: {r.long_caja}×{r.ancho_caja}×{r.altura_caja}, Barra: {r.long_barra}×{r.ancho_barra}, Peso: {r.peso} kg
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => handleEdit(r)}>
                <Pencil size={16} />
              </Button>
              <Button size="sm" variant="destructive" onClick={() => handleDelete(r.id)}>
                <Trash2 size={16} />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
