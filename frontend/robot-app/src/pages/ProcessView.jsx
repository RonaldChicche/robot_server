import { useState, useEffect, useRef  } from "react"
import socket from "@/lib/socket"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Terminal } from "lucide-react"
import { Switch } from "@/components/ui/switch"

export default function ProcesoView() {
  const [form, setForm] = useState({
    long_caja: 1100,
    ancho_caja: 150.0,
    long_barra: 1000.0,
    ancho_barra: 50.0,
    espesor: 10.0,
    peso: 10.0,
    cantidad_x: 1,
    cantidad_z: 1,
    no_carro: 1
  })

  const [consoleOutput, setConsoleOutput] = useState([])
  const [open, setOpen] = useState(false)
  const [monitor, setMonitor] = useState({
    conteo_stack_x: 0,
    conteo_stack_z: 0,
    codigo_alarma: 0,
    significado_alarma: "Normal",
    torque_j: [0, 0, 0, 0, 0, 0],
    estado_inicio: false,
    estado_layer: false,
    estado_fin: false,
    bit_stack: false,
    bit_coordinador: false
  })

  const updateField = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const sendButton = (nameButton) => {
    fetch(`http://localhost:5000/api/kafka/01/${nameButton}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    })
      .then(res => res.json())
      .then(data => {
        console.log("Servidor respondió:", data)
        setConsoleOutput(prev => [...prev, `✅ Proceso iniciado correctamente: ${JSON.stringify(data)}`])
      })
      .catch(err => {
        setConsoleOutput(prev => [...prev, `❌ Error al iniciar proceso: ${err.message}`])
      })
  }

  const sendData = () => {
    const payload = {
      type: "process",
      name: "send_data",
      params: form,
    }

    fetch("http://localhost:5000/api/kafka/send-process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        console.log("Servidor respondió:", data)
        setConsoleOutput(prev => [...prev, `✅ Datos enviados correctamente: ${JSON.stringify(payload)}`])
      })
      .catch(err => {
        setConsoleOutput(prev => [...prev, `❌ Error al enviar datos: ${err.message}`])
      })
  }

  const toggleBit = (bit, value) => {
    console.log(`🛰 Enviando bit ${bit} con valor ${value}`) // <-- agrega esto

    fetch(`http://localhost:5000/api/kafka/01/${bit}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "value": value })
    })
      .then(() => {
        setMonitor(prev => {
          if (bit === "toggle-stack-bit") {
            return { ...prev, bit_stack: value }
          } else if (bit === "toggle-coord-bit") {
            return { ...prev, bit_coordinador: value }
          }
          return prev
        })
      })
      .catch((err) => {
        console.log("❌ Error en fetch:", err)
        setConsoleOutput(prev => [...prev, `⚠️ Error al actualizar bit ${bit}`])
      })
  }


  const prevAlarmaRef = useRef(0)

  useEffect(() => {
    socket.on("status:01", (data) => {
      //console.log(data)
      const alarma = data.status?.alarm_code ?? 0

      setMonitor((prev) => {
        if (alarma !== prevAlarmaRef.current) {
          prevAlarmaRef.current = alarma
          fetch(`http://localhost:5000/api/alarm/${alarma}`)
            .then((res) => res.json())
            .then((alarm) => {
              setMonitor((m) => ({
                ...m,
                significado_alarma: alarm.message || "Error",
                codigo_alarma: alarma,
              }))
            })
            .catch(() => {
              setMonitor((m) => ({
                ...m,
                significado_alarma: "Error",
                codigo_alarma: alarma,
              }))
            })
        }

        return {
          ...prev,
          codigo_alarma: alarma,
          conteo_stack_x: data.counters?.["counter-0"]?.current ?? 0,
          conteo_stack_z: data.counters?.["counter-1"]?.current ?? 0,
          estado_inicio: data.status?.outputs?.y30 === 1,
          estado_layer: data.status?.outputs?.y32 === 1,
          estado_fin: data.status?.outputs?.y33 === 1,
          torque_j : Array.from({ length: 6 }, (_, i) => data.axis_torque?.[i] ?? 0),
          bit_stack: data.status?.outputs?.y42 === 1,
          bit_coordinador: data.status?.outputs?.y41 === 1,
        }
      })
    })

    return () => {
      socket.off("status:01")
    }
  }, [])


  const renderStateDot = (active) => (
    <div className={`w-3 h-3 rounded-full ${active ? "bg-green-500" : "bg-gray-500"}`}></div>
  )

  return (
    <div className="w-full max-w-screen-xl mx-auto p-4 sm:p-6 px-4 sm:px-20">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 sm:gap-6">
        <div className="flex flex-col gap-3">
          <Button onClick={() => sendButton("start_button")} className="bg-cyan-600 hover:bg-cyan-700">Start</Button>
          <Button onClick={() => sendButton("pause_button")} variant="secondary">Pause</Button>
          <Button onClick={() => sendButton("stop_button")} variant="destructive">Stop</Button>
          <Button onClick={() => sendButton("clear_alarm_button")} variant="secondary">Clear Alarm</Button>

          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-white">Bit Stack</span>
              <Switch
                checked={monitor.bit_stack}
                onCheckedChange={(val) => toggleBit("toggle-stack-bit", val)}
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white">Bit Coordinador</span>
              <Switch
                checked={monitor.bit_coordinador}
                onCheckedChange={(val) => {
                  toggleBit("toggle-coord-bit", val)
                  setMonitor((prev) => ({ ...prev, bit_coordinador: val }))
                }}
              />
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-4 sm:p-6 space-y-6 md:col-span-2">
          <h2 className="text-xl font-bold text-white">Parámetros del Proceso</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              ["long_caja", "Longitud Caja"],
              ["ancho_caja", "Ancho Caja"],
              ["long_barra", "Longitud Barra"],
              ["ancho_barra", "Ancho Barra"],
              ["espesor", "Espesor"],
              ["peso", "Peso"],
              ["cantidad_x", "Cantidad X"],
              ["cantidad_z", "Cantidad Z"],
              ["no_carro", "No. Carro"],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="text-sm font-semibold text-white mb-1 block">{label}</label>
                <Input
                  type="number"
                  value={form[key]}
                  min={"cantidad_x" === key || "cantidad_z" === key ? 1 : undefined}
                  onChange={(e) => updateField(key, parseFloat(e.target.value))}
                />
              </div>
            ))}
          </div>
          <Button onClick={sendData} className="bg-cyan-600 hover:bg-cyan-700">
            Enviar Datos
          </Button>
        </div>

        <div className="bg-slate-800 rounded-xl p-4 sm:p-6 space-y-4 md:col-span-2 text-white">
          <h2 className="text-xl font-bold">Monitoreo</h2>
          <p><strong>Conteo Stack X:</strong> {monitor.conteo_stack_x}</p>
          <p><strong>Conteo Stack Z:</strong> {monitor.conteo_stack_z}</p>
          <div className={monitor.codigo_alarma !== 0 ? "bg-red-700 p-2 rounded" : ""}>
            <p><strong>Código de Alarma:</strong> {monitor.codigo_alarma}</p>
            <p><strong>Significado:</strong> {monitor.significado_alarma}</p>
          </div>
          <div>
            <strong>Torque por Junte:</strong>
            <table className="w-full text-sm mt-2">
              <thead>
                <tr className="text-left text-cyan-400">
                  <th>Junte</th>
                  <th>Torque</th>
                </tr>
              </thead>
              <tbody>
                {monitor.torque_j.map((val, idx) => (
                  <tr key={idx} className={val > 80 ? "bg-red-600 text-white" : ""}>
                    <td>J{idx + 1}</td>
                    <td>{val} A</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between pt-4">
            <span className="text-white">Bit Inicio</span>
            {renderStateDot(monitor.estado_inicio)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-white">Bit Layer Terminado</span>
            {renderStateDot(monitor.estado_layer)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-white">Bit Fin</span>
            {renderStateDot(monitor.estado_fin)}
          </div>
        </div>
      </div>

      <Collapsible open={open} onOpenChange={setOpen} className="mt-6">
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="flex items-center gap-2">
            <Terminal size={16} />
            {open ? "Ocultar consola" : "Mostrar consola"}
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="bg-black text-green-400 mt-2 rounded-md p-4 font-mono text-sm max-h-64 overflow-auto">
          {consoleOutput.length > 0 ? (
            <ul className="space-y-1">
              {consoleOutput.map((line, idx) => (
                <li key={idx}>{line}</li>
              ))}
            </ul>
          ) : (
            <p className="italic text-gray-500">Sin mensajes aún...</p>
          )}
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}
