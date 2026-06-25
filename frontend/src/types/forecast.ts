export interface ForecastSummary {
  candidates: number;
  modeled_items: number;
  excluded_items: number;
  average_wape: number;
  average_mae: number;
  average_rmse: number;
  average_bias: number;
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  most_frequent_best_model: string;
  best_average_model: string;
  forecast_horizon: number;
  forecast_records: number;
  first_forecast_period: string;
  last_forecast_period: string;
}

export interface ForecastCandidate {
  item_code: string;
  item_name: string;
  item_group?: string | null;
  last_sale_period?: string | null;
  abc_xyz_class: string;
  data_quality_status: string;
  best_model?: string | null;
  best_wape?: number | null;
  best_mae?: number | null;
  forecast_confidence?: string | null;
}

export interface ForecastResultPoint {
  item_code: string;
  item_name: string;
  forecast_period: string;
  forecast_quantity: number;
  forecast_confidence: string;
}

export interface ForecastPoint {
  period?: string;
  forecast_period?: string;
  net_quantity?: number;
  forecast_quantity?: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface ForecastItemDetail {
  item: ForecastCandidate;
  historical: Array<ForecastPoint & { period: string; net_quantity: number }>;
  test: Array<ForecastPoint & { period: string; net_quantity: number }>;
  best_model: {
    best_model: string;
    best_wape?: number | null;
    best_mae?: number | null;
    best_rmse?: number | null;
    forecast_confidence: string;
  } | null;
  future_forecast: Array<
    ForecastPoint & {
      forecast_period: string;
      forecast_quantity: number;
    }
  >;
}
