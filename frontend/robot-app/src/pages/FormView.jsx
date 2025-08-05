import { useState, useEffect } from "react"
import { API_BASE_URL } from "@/config"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function FormView() {
  const [robotId, setRobotId] = useState("01")
  const [methods, setMethods] = useState([])
  const [selectedMethod, setSelectedMethod] = useState(null)
  const [params, setParams] = useState({})
  //const [showParams, setShowParams] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/methods`)
      .then((res) => res.json())
      .then((data) => setMethods(data))
      .catch((err) => console.error("❌ Error cargando métodos:", err))
  }, [])

  useEffect(() => {
    if (selectedMethod && selectedMethod.requires_params) {
      fetch(`${API_BASE_URL}/api/methods/${selectedMethod.id}/parameters`)
        .then((res) => res.json())
        .then((data) => {
          const initialParams = {}
          data.forEach((p) => {
            initialParams[p.name] = p.default_value || ""
          })
          setParams(initialParams)
        })
        .catch((err) => console.error("❌ Error cargando parámetros:", err))
    } else {
      setParams({})
    }
  }, [selectedMethod])

  const handleParamChange = (key, value) => {
    setParams((prev) => ({ ...prev, [key]: value }))
  }

  const sendToKafka = async () => {
    const timestamp = new Date().toISOString()
    const ids = robotId.split(",").map((id) => id.trim())

    for (const id of ids) {
      const pickKeys = ["pick_x", "pick_y", "pick_z", "pick_rx", "pick_ry", "pick_rz"]
      const putKeys = ["put_x", "put_y", "put_z", "put_rx", "put_ry", "put_rz"]

      const pick = []
      const put = []
      const rest = {}

      Object.entries(params).forEach(([key, val]) => {
        if (val.trim() !== "") {
          let parsed
          try {
            parsed = JSON.parse(val)
          } catch {
            parsed = val
          }

          if (pickKeys.includes(key)) {
            pick[pickKeys.indexOf(key)] = parsed
          } else if (putKeys.includes(key)) {
            put[putKeys.indexOf(key)] = parsed
          } else {
            rest[key] = parsed
          }
        }
      })

      const orderedParams = {}
      if (pick.length) orderedParams.pick = pick
      if (put.length) orderedParams.put = put
      Object.assign(orderedParams, rest)

      const data_msg = {
        order_id: `ORD_${timestamp.replace(/[-:.TZ]/g, "")}_${selectedMethod.name}_${id}`,
        robot_id: id,
        type: selectedMethod.type,
        name: selectedMethod.name,
        params: orderedParams,
        timestamp,
      }

      try {
        const res = await fetch(`${API_BASE_URL}/api/kafka/send-method`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data_msg),
        })

        if (!res.ok) throw new Error("Error al enviar")
      } catch (err) {
        console.error("❌ Error:", err)
        alert("❌ Fallo al enviar")
      }
    }

    alert("✅ Mensaje(s) enviado(s)")
  }


  return (
    <div className="p-6 max-w-xl mx-auto">
      <Card className="bg-slate-900 border-slate-800 text-slate-100">
        <CardHeader>
          <CardTitle>Enviar mensaje a Kafka</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col space-y-6">
          <div className="flex flex-col space-y-2">
            <Label htmlFor="robotId">Robot ID(s)</Label>
            <Input
              id="robotId"
              placeholder="Ej: 01 o 01,02,03"
              value={robotId}
              onChange={(e) => setRobotId(e.target.value)}
            />
          </div>

          <div className="flex flex-col space-y-2">
            <Label htmlFor="method">Comando</Label>
            <Select onValueChange={(val) => setSelectedMethod(methods.find((m) => m.name === val))}>
              <SelectTrigger id="method">
                <SelectValue placeholder="Selecciona un método" />
              </SelectTrigger>
              <SelectContent>
                {methods.map((m) => (
                  <SelectItem key={m.id} value={m.name}>
                    {m.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedMethod && (
            <div className="flex flex-col space-y-2 text-sm text-slate-300">
              <Separator className="my-2 bg-slate-700" />
              <div>
                <strong>Tipo:</strong> {selectedMethod.type}
              </div>
              <div>
                <strong>Descripción:</strong> {selectedMethod.description}
              </div>
            </div>
          )}

          {selectedMethod?.requires_params && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-80 overflow-y-auto pr-2">
              {Object.keys(params).map((key) => (
                <div key={key} className="flex flex-col space-y-2">
                  <Label htmlFor={key}>{key}</Label>
                  <Input
                    id={key}
                    placeholder={key}
                    value={params[key]}
                    onChange={(e) => handleParamChange(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={sendToKafka}
            disabled={!selectedMethod}
            className="bg-white text-black hover:bg-transparent hover:text-white hover:border hover:border-white transition-all"
          >
            Enviar
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}