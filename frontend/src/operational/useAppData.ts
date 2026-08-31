import { useEffect, useState } from "react";
import { getAppDataSnapshot, loadInitialAppData, subscribeAppData } from "./appDataStore";

export function useAppData() {
  const [data, setData] = useState(getAppDataSnapshot);

  useEffect(() => {
    const unsubscribe = subscribeAppData(() => setData(getAppDataSnapshot()));
    void loadInitialAppData();
    return unsubscribe;
  }, []);

  return data;
}
