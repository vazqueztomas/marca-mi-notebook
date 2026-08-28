const SPECS: [string, string][] = [
  ['Modelo', 'MacBook Air'],
  ['Chip', 'Apple M5 — CPU 10 núcleos'],
  ['Memoria', '16 GB unificada'],
  ['Almacenamiento', '512 GB SSD'],
]

export default function TheMachine() {
  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-2">La máquina</h2>
      <p className="text-ink-soft text-sm mb-6">
        La notebook que estoy financiando con esto. Estas son las specs que voy a comprar.
      </p>

      <div className="grid sm:grid-cols-2 gap-6">
        <div className="bg-surface p-4 rounded-lg border border-border">
          <dl className="divide-y divide-border">
            {SPECS.map(([label, value]) => (
              <div key={label} className="flex justify-between py-2 text-sm">
                <dt className="text-ink-soft">{label}</dt>
                <dd className="font-semibold">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="bg-surface p-4 rounded-lg border border-border text-sm text-ink-soft space-y-2">
          <p>
            Lo que se recauda ayuda a financiarla y a lo que sigue: los viajes y proyectos en los que la notebook
            me acompaña.
          </p>
        </div>
      </div>
    </section>
  )
}
