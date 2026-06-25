import { BookOpenCheck, Boxes, ChartSpline, CircleAlert, PackagePlus, ShieldCheck } from "lucide-react";

const concepts = [
  { icon: PackagePlus, title: "Compra sugerida activa", text: "Cantidad calculada con forecast de confianza media, inventario y stock de seguridad. Requiere aprobación humana." },
  { icon: CircleAlert, title: "Compra referencial", text: "Existe necesidad potencial, pero el forecast tiene confianza baja. Debe revisarse antes de comprar." },
  { icon: ShieldCheck, title: "Confianza", text: "Resume el error histórico del modelo. Media permite un piloto controlado; baja exige cautela." },
  { icon: ChartSpline, title: "Cobertura", text: "Días estimados que el stock disponible puede atender según la demanda proyectada." },
  { icon: Boxes, title: "Sobrestock", text: "Cobertura superior a 180 días. Puede indicar capital inmovilizado o baja rotación." },
  { icon: BookOpenCheck, title: "ABC / XYZ", text: "ABC mide importancia por volumen; XYZ mide estabilidad. Juntos orientan el método de forecast y la prioridad." },
];

export function InterpretationPage() {
  return (
    <div className="page-stack">
      <section className="hero-panel interpretation-hero">
        <div><span className="eyebrow">Guía rápida</span><h2>Cómo interpretar el portal</h2><p>Una traducción directa de los indicadores analíticos al lenguaje operativo.</p></div>
      </section>
      <section className="concept-grid">
        {concepts.map(({ icon: Icon, title, text }) => (
          <article className="concept-card" key={title}>
            <div className="concept-icon"><Icon size={22} /></div>
            <h3>{title}</h3>
            <p>{text}</p>
          </article>
        ))}
      </section>
      <section className="panel interpretation-panel">
        <h3>Principios de uso</h3>
        <ul>
          <li>El portal no escribe ni crea documentos en SAP.</li>
          <li>Las compras de baja confianza nunca se presentan como automáticas.</li>
          <li>Los importes monetarios no se muestran hasta validar costos y moneda.</li>
          <li>Las recomendaciones deben contrastarse con restricciones comerciales y operativas.</li>
        </ul>
      </section>
    </div>
  );
}
