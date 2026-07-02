import type { ReactNode } from "react";

interface BusinessExplanationCardProps {
  title: string;
  description?: string;
  items?: string[];
  children?: ReactNode;
}

export function BusinessExplanationCard({
  title,
  description,
  items,
  children,
}: BusinessExplanationCardProps) {
  return (
    <article className="business-explanation-card">
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {items && (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
      {children}
    </article>
  );
}
