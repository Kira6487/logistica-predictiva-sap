export interface ReplenishmentItem {
  item_code: string;
  item_name: string;
  item_group?: string | null;
  warehouse_code: string;
  warehouse_name: string;
  available_stock: number;
  physical_stock: number;
  committed_stock: number;
  on_order_stock: number;
  projected_stock: number;
  projected_demand_horizon: number;
  coverage_days?: number | null;
  safety_stock: number;
  suggested_purchase_quantity: number;
  suggested_purchase_raw: number;
  stock_status: string;
  recommendation_type: string;
  recommendation_reason: string;
  forecast_confidence: string;
  priority_score: number;
  priority_level: string;
  abc_class_quantity: string;
  abc_class_amount: string;
  xyz_class: string;
  abc_xyz_class: string;
  data_quality_status: string;
  model_used: string;
  requires_manual_review: boolean;
  [key: string]: unknown;
}

export interface ReplenishmentDetail {
  replenishment: ReplenishmentItem;
  forecast: Array<{
    forecast_period: string;
    forecast_quantity: number;
    lower_bound: number;
    upper_bound: number;
    model_used: string;
    forecast_confidence: string;
  }>;
}
