export interface ReplenishmentSummary {
  total_items_evaluated: number;
  items_with_purchase: number;
  active_purchase_suggestions: number;
  referential_purchases: number;
  critical_items: number;
  review_items: number;
  healthy_items: number;
  overstock_items: number;
  no_demand_items: number;
  not_recommended_items: number;
  total_suggested_quantity: number;
  medium_confidence_items: number;
  low_confidence_items: number;
  high_confidence_items: number;
  manual_review_items: number;
  high_priority_items: number;
  medium_priority_items: number;
  low_priority_items: number;
  horizon_months: number;
}

export interface HealthResponse {
  status: string;
  service: string;
}
