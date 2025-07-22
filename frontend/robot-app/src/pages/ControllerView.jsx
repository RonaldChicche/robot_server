import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"

export default function ControllerView() {
  const [form, setForm] = useState({
    pick: ["", "", "", "", "", ""],
    put: ["", "", "", "", "", ""],
    cantidad_z: 1,
    cantidad_x: 1,
    dx: 0,
    dy: 0,
    espesor: 0,
    ancho: 0,
    velocidad: 100,
    bit_coordinador: false,
  })

  const [bitStack, setBitStack] = useState(false)

  const updateField = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
    console.log(form)
  }

  const updateArrayField = (field, index, value) => {
    setForm(prev => {
      const updated = [...prev[field]]
      updated[index] = value
      return { ...prev, [field]: updated }
    })
  }

  const sendCommand = (cmd) => {
    fetch("http://localhost:5000/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "method", name: cmd })
    })
  }

  const sendData = () => {
    fetch("http://localhost:5000/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "process",
        name: "send_data",
        data: form,
      })
    })
  }

  return (
    <div className="w-full max-w-screen-xl mx-auto p-6 px-20 ">
    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="flex flex-col gap-3 md:col-span-1">
        <Button onClick={() => sendCommand("startButton")} className="bg-cyan-600 hover:bg-cyan-700">Start Button</Button>
        <Button onClick={() => sendCommand("pauseButton")} variant="secondary">Pause Button</Button>
        <Button onClick={sendData} className="bg-cyan-600 hover:bg-cyan-700">Send Data</Button>
        <Button onClick={() => sendCommand("clearAlarm")} variant="secondary">Clear Alarm</Button>
        <Button onClick={() => sendCommand("stopButton")} variant="destructive">Stop Button</Button>

        <div className="space-y-6 mt-6">
          <div className="flex items-center justify-between">
            <span>Bit Stack</span>
            <Switch
              checked={bitStack}
              onCheckedChange={(val) => {
                setBitStack(val)
                fetch("http://localhost:5000/api/switch", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ bit: "stack", value: val })
                })
              }}
            />
          </div>
          <div className="flex items-center justify-between">
            <span>Bit Coordinador</span>
            <Switch
              checked={form.bit_coordinador}
              onCheckedChange={(val) => {
                updateField("bit_coordinador", val)
                fetch("http://localhost:5000/api/switch", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ bit: "coordinador", value: val })
                })
              }}
            />
          </div>
        </div>
      </div>        

      <div className="bg-slate-800 rounded-xl p-4 space-y-4 md:col-span-2">
        <div>
          <label className="font-bold">Pick</label>
          <div className="grid grid-cols-6 gap-2 mt-2">
            {form.pick.map((val, i) => (
              <Input
                key={i}
                placeholder="-"
                value={val}
                onChange={(e) => updateArrayField("pick", i, e.target.value)}
              />
            ))}
          </div>
        </div>

        <div>
          <label className="font-bold">Put</label>
          <div className="grid grid-cols-6 gap-2 mt-2">
            {form.put.map((val, i) => (
              <Input
                key={i}
                placeholder="-"
                value={val}
                onChange={(e) => updateArrayField("put", i, e.target.value)}
              />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-semibold mb-1 block">Cantidad Z</label>
            <Input
              type="number"
              min={1}
              value={form.cantidad_z}
              onChange={(e) => updateField("cantidad_z", parseInt(e.target.value))}
            />
          </div>

          <div>
            <label className="text-sm font-semibold mb-1 block">Cantidad X</label>
            <Input
              type="number"
              min={1}
              value={form.cantidad_x}
              onChange={(e) => updateField("cantidad_x", parseInt(e.target.value))}
            />
          </div>

          <div>
            <label className="text-sm font-semibold mb-1 block">dx</label>
            <Input
              type="number"
              value={form.dx}
              onChange={(e) => updateField("dx", parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label className="text-sm font-semibold mb-1 block">dy</label>
            <Input
              type="number"
              value={form.dy}
              onChange={(e) => updateField("dy", parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label className="text-sm font-semibold mb-1 block">Ancho</label>
            <Input
              type="number"
              value={form.ancho}
              onChange={(e) => updateField("ancho", parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label className="text-sm font-semibold mb-1 block">Espesor</label>
            <Input
              type="number"
              value={form.espesor}
              onChange={(e) => updateField("espesor", parseFloat(e.target.value))}
            />
          </div>
        </div>

        <div>
          <label className="block mb-1 font-bold">Velocidad</label>
          <Slider
            min={0}
            max={1000}
            step={1}
            value={[form.velocidad]}
            onValueChange={([val]) => updateField("velocidad", val)}
          />
          <div className="text-right text-sm">{form.velocidad}</div>
        </div>

        <div className="flex items-center gap-2">
          <Checkbox
            checked={form.bit_coordinador}
            onCheckedChange={(val) => updateField("bit_coordinador", val)}
          />
          <span>Bit Coordinador</span>
        </div>
      </div>
      


    </div>
    </div>
  )
}
