export interface InventoryItem {
  item_code: string;
  item_name: string;
  item_group?: string | null;
  warehouse_code: string;
  warehouse_name: string;
  physical_stock: number;
  committed_stock: number;
  on_order_stock: number;
  available_stock: number;
  projected_stock: number;
}
