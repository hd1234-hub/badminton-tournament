import { useState, useEffect, useCallback } from "react";
import type { Competition } from "../types";
import * as compApi from "../api/competitions";

export function useCompetition(id: number | undefined) {
  const [comp, setComp] = useState<Competition | null>(null);

  const refresh = useCallback(() => {
    if (id) compApi.getCompetition(id).then(setComp);
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  return { comp, refresh };
}
