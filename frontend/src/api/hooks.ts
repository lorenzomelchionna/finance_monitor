import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

/** An instrument plus its ledger-derived position (quantity, cost).
 * Distinct from the portfolio summary's PositionOut, which is a *valued*
 * position (market value, P/L, XIRR). */
export type PositionOut = components["schemas"]["InstrumentPositionOut"];
export type InstrumentOut = components["schemas"]["InstrumentOut"];
export type PortfolioSummaryOut = components["schemas"]["PortfolioSummaryOut"];
export type PriceStatusOut = components["schemas"]["PriceStatusOut"];
export type MonteCarloRequest = components["schemas"]["MonteCarloRequest"];
export type MonteCarloResponse = components["schemas"]["MonteCarloResponse"];
export type PortfolioHistoryOut = components["schemas"]["PortfolioHistoryOut"];
export type InstrumentHistoryOut = components["schemas"]["InstrumentHistoryOut"];
export type TransactionOut = components["schemas"]["TransactionOut"];
export type ImportResultOut = components["schemas"]["ImportResultOut"];
export type CompositionOut = components["schemas"]["CompositionOut"];
export type CompositionRefreshOut = components["schemas"]["CompositionRefreshOut"];

const POSITIONS_KEY = ["positions"] as const;
const INSTRUMENTS_KEY = ["instruments"] as const;
const PORTFOLIO_SUMMARY_KEY = ["portfolio", "summary"] as const;
const PORTFOLIO_HISTORY_KEY = ["portfolio", "history"] as const;
const TRANSACTIONS_KEY = ["transactions"] as const;
const COMPOSITION_KEY = ["composition"] as const;

export function usePositions() {
  return useQuery({
    queryKey: POSITIONS_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/positions");
      if (error) throw error;
      return data;
    },
  });
}

export function useInstruments() {
  return useQuery({
    queryKey: INSTRUMENTS_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/instruments");
      if (error) throw error;
      return data;
    },
  });
}

/** Patch instrument metadata: rename, set the pricing ticker, or
 * include/exclude it from the portfolio. Every field is optional, so
 * callers send only what changed. */
export function useUpdateInstrument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...patch
    }: {
      id: number;
      name?: string;
      ticker?: string;
      included?: boolean;
    }) => {
      const { data, error } = await api.PUT("/api/instruments/{instrument_id}", {
        params: { path: { instrument_id: id } },
        body: patch,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Changing what is tracked moves every downstream number.
      for (const key of [POSITIONS_KEY, INSTRUMENTS_KEY, PORTFOLIO_SUMMARY_KEY, PORTFOLIO_HISTORY_KEY, COMPOSITION_KEY]) {
        queryClient.invalidateQueries({ queryKey: key });
      }
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

export function useComposition() {
  return useQuery({
    queryKey: COMPOSITION_KEY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/composition");
      if (error) throw error;
      return data;
    },
  });
}

export function useRefreshComposition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/api/composition/refresh");
      if (error) throw error;
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: COMPOSITION_KEY }),
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
      queryClient.invalidateQueries({ queryKey: POSITIONS_KEY });
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
      queryClient.invalidateQueries({ queryKey: POSITIONS_KEY });
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
