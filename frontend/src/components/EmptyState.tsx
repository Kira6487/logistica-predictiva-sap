import { PackageOpen } from "lucide-react";

export function EmptyState({ message = "No hay datos para mostrar." }: { message?: string }) {
  return (
    <div className="state-card">
      <PackageOpen size={30} />
      <p>{message}</p>
    </div>
  );
}
