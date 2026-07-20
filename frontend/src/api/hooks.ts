import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

export type HoldingOut = components["schemas"]["HoldingOut"];
export type HoldingCreate = components["schemas"]["HoldingCreate"];
export type HoldingUpdate = components["schemas"]["HoldingUpdate"];

const HOLDINGS_KEY = ["holdings"] as const;

export function useHoldings() {
  return useQuery({
    queryKey: HOLDINGS_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/holdings");
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: HoldingCreate) => {
      const { data, error } = await api.POST("/api/holdings", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY }),
  });
}

export function useUpdateHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: HoldingUpdate }) => {
      const { data, error } = await api.PUT("/api/holdings/{holding_id}", {
        params: { path: { holding_id: id } },
        body,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY }),
  });
}

export function useDeleteHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { error } = await api.DELETE("/api/holdings/{holding_id}", {
        params: { path: { holding_id: id } },
      });
      if (error) throw error;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY }),
  });
}
