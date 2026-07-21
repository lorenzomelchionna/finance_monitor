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
export type PortfolioHistoryOut = components["schemas"]["PortfolioHistoryOut"];
export type InstrumentHistoryOut = components["schemas"]["InstrumentHistoryOut"];
export type TransactionOut = components["schemas"]["TransactionOut"];
export type ImportResultOut = components["schemas"]["ImportResultOut"];

const HOLDINGS_KEY = ["holdings"] as const;
const PORTFOLIO_SUMMARY_KEY = ["portfolio", "summary"] as const;
const PORTFOLIO_HISTORY_KEY = ["portfolio", "history"] as const;
const TRANSACTIONS_KEY = ["transactions"] as const;

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
    mutationFn: async ({ id, name, ticker }: { id: number; name: string; ticker?: string }) => {
      const { data, error } = await api.PUT("/api/instruments/{instrument_id}", {
        params: { path: { instrument_id: id } },
        body: { name, ticker },
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

export function usePortfolioHistory() {
  return useQuery({
    queryKey: PORTFOLIO_HISTORY_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/portfolio/history");
      if (error) throw error;
      return data;
    },
    // Full max-history is expensive to fetch (yfinance, ~1s/ticker) and
    // rarely changes intraday — cache generously; horizon/smoothing are
    // client-side so they never re-hit this.
    staleTime: 1000 * 60 * 30,
  });
}

export function useTransactions() {
  return useQuery({
    queryKey: TRANSACTIONS_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/transactions");
      if (error) throw error;
      return data;
    },
  });
}

export function useImportTransactions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append("file", file);
      const { data, error } = await api.POST("/api/transactions/import", {
        body: body as unknown as { file: string },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSACTIONS_KEY });
      queryClient.invalidateQueries({ queryKey: PORTFOLIO_SUMMARY_KEY });
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
