import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

export type HoldingOut = components["schemas"]["HoldingOut"];
export type HoldingCreate = components["schemas"]["HoldingCreate"];
export type HoldingUpdate = components["schemas"]["HoldingUpdate"];
export type PortfolioSummaryOut = components["schemas"]["PortfolioSummaryOut"];
export type PriceStatusOut = components["schemas"]["PriceStatusOut"];
export type MonteCarloRequest = components["schemas"]["MonteCarloRequest"];
export type MonteCarloResponse = components["schemas"]["MonteCarloResponse"];

const HOLDINGS_KEY = ["holdings"] as const;
const PORTFOLIO_SUMMARY_KEY = ["portfolio", "summary"] as const;

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY });
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
    },
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY });
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
    },
  });
}

export function useUpdateInstrument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, name }: { id: number; name: string }) => {
      const { data, error } = await api.PUT("/api/instruments/{instrument_id}", {
        params: { path: { instrument_id: id } },
        body: { name },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY });
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
    },
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY });
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
    },
  });
}

export function usePortfolioSummary() {
  return useQuery({
    queryKey: PORTFOLIO_SUMMARY_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/portfolio/summary");
      if (error) throw error;
      return data;
    },
  });
}

export function useRefreshPrices() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/api/prices/refresh");
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
      queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY });
    },
  });
}

export function useSetManualPrice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      instrumentId,
      price,
      currency,
    }: {
      instrumentId: number;
      price: number;
      currency: string;
    }) => {
      const { data, error } = await api.PUT("/api/prices/{instrument_id}", {
        params: { path: { instrument_id: instrumentId } },
        body: { price, currency },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
      queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY });
    },
  });
}

export function useRunMontecarlo() {
  return useMutation({
    mutationFn: async (body: MonteCarloRequest) => {
      const { data, error } = await api.POST("/api/simulation/montecarlo", { body });
      if (error) throw error;
      return data;
    },
  });
}
