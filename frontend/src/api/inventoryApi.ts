import { apiGet } from "./client";
import type { InventoryItem } from "../types/inventory";

export const inventoryApi = {
  current: (onlyWithStock = true) =>
    apiGet<InventoryItem[]>("/inventory/current", {
      only_with_stock: onlyWithStock,
    }),
};
