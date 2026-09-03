"use client";

import React, { useState, useEffect } from "react";
import ProductCard from "@/components/ProductCard";
import { fetchCatalog, fetchStoreBCatalog, fetchAgentSpec, Product } from "@/lib/api";

export default function CatalogAPI() {
  const [activeTab, setActiveTab] = useState<"storeA" | "storeB">("storeA");
  const [storeAProducts, setStoreAProducts] = useState<Product[]>([]);
  const [storeBProducts, setStoreBProducts] = useState<Product[]>([]);
  const [agentSpec, setAgentSpec] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [catA, catB] = await Promise.all([
          fetchCatalog(false),
          fetchStoreBCatalog(),
        ]);
        setStoreAProducts(catA.products || []);
        setStoreBProducts(catB.products || []);
      } catch (e) {
        console.error("Failed to load catalogs:", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleFetchSpec = async () => {
    try {
      const spec = await fetchAgentSpec();
      setAgentSpec(spec);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-[1200px]">
      <div>
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Federated Multi-Merchant Product Network
        </h2>
        <p className="text-xs text-[var(--text-secondary)] mt-0.5">
          Structured JSON attributes consumed directly by autonomous AI buyer agents across federated partner stores.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[var(--border-color)] pb-2">
        <button
          onClick={() => setActiveTab("storeA")}
          className={`text-xs px-3 py-1.5 rounded-md transition font-medium ${
            activeTab === "storeA"
              ? "bg-[var(--bg-pill)] text-[var(--text-primary)] shadow-[var(--card-shadow)]"
              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          Store A: Aura Artisan Teas (Primary)
        </button>
        <button
          onClick={() => setActiveTab("storeB")}
          className={`text-xs px-3 py-1.5 rounded-md transition font-medium ${
            activeTab === "storeB"
              ? "bg-[var(--bg-pill)] text-[var(--text-primary)] shadow-[var(--card-shadow)]"
              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          Store B: Botanical Leaf Co. (Federated Partner)
        </button>
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="text-xs text-[var(--text-secondary)] py-8">Loading product catalog...</div>
      ) : activeTab === "storeA" ? (
        <div className="grid grid-cols-4 gap-4">
          {storeAProducts.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {storeBProducts.map((p) => (
            <ProductCard key={p.id} product={p} isStoreB />
          ))}
        </div>
      )}

      {/* Agent Spec Discovery */}
      <div className="pt-4 border-t border-[var(--border-color)]">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">
            Agent API Metadata Discovery (<code className="font-mono text-xs text-[#00baf2]">GET /agent-spec</code>)
          </h3>
          <button
            onClick={handleFetchSpec}
            className="text-xs bg-[var(--bg-card)] hover:bg-[var(--bg-pill)] text-[var(--text-primary)] px-3 py-1.5 rounded-md border border-[var(--border-color)] transition shadow-[var(--card-shadow)]"
          >
            Fetch Agent Specification
          </button>
        </div>

        {agentSpec && (
          <pre className="bg-[var(--code-bg)] border border-[var(--border-color)] p-4 rounded-xl text-xs font-mono text-[var(--success-text)] overflow-x-auto max-h-[300px] shadow-[var(--card-shadow)]">
            {JSON.stringify(agentSpec, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
