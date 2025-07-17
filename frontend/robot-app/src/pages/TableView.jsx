export default function TableView() {
  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4 text-slate-100">Parámetros del sistema</h2>
      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-slate-900 text-slate-300 text-left text-sm uppercase">
            <tr>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Valor</th>
              <th className="px-4 py-3">Fuente</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {/* Ejemplo de fila vacía */}
            {/* <tr>
              <td className="px-4 py-2">temperatura_motor</td>
              <td className="px-4 py-2">64 °C</td>
              <td className="px-4 py-2">Redis</td>
            </tr> */}
          </tbody>
        </table>
      </div>
    </div>
  );
}
