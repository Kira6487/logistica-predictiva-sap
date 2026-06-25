export interface AnalyticsSummary {
  total_items_analyzed: number;
  items_a: number;
  items_b: number;
  items_c: number;
  items_x: number;
  items_y: number;
  items_z: number;
  intermittent_items: number;
  insufficient_history_items: number;
  negative_demand_items: number;
  amount_anomaly_items: number;
  forecast_recommended_items: number;
  forecast_not_recommended_items: number;
  date_from: string;
  date_to: string;
  total_months_available: number;
}

export interface AnalyticsItem {
  item_code: string;
  item_name: string;
  item_group?: string | null;
  abc_quantity_class?: string;
  abc_amount_class?: string;
  xyz_class?: string;
  abc_xyz_class?: string;
  data_quality_status: string;
  recommended_for_forecast?: boolean;
  net_quantity_total?: number;
  coefficient_of_variation?: number | null;
}
