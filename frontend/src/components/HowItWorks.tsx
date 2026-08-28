const STEPS = [
  {
    title: 'Elegí tu lugar y tamaño',
    body: 'Diez lugares en tres tamaños, con precio según tamaño y visibilidad.',
  },
  {
    title: 'Ganá la puja',
    body: 'La oferta más alta se lleva el lugar. Pagás online y listo.',
  },
  {
    title: 'Tu sticker viaja conmigo',
    body: 'Imprimo tu logo en un sticker de vinilo troquelado y lo pego en la notebook. A todos lados que vaya, tu marca va conmigo.',
  },
]

export default function HowItWorks() {
  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-6">Cómo funciona</h2>
      <div className="grid sm:grid-cols-3 gap-4">
        {STEPS.map((step, i) => (
          <div key={step.title} className="bg-surface p-4 rounded-lg border border-border">
            <div className="text-sm font-semibold text-celeste mb-1">{i + 1}</div>
            <h3 className="font-bold mb-2">{step.title}</h3>
            <p className="text-ink-soft text-sm">{step.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
