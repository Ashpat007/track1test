import React from "react";
import { Product } from "@/lib/api";

interface ProductCardProps {
  product: Product;
  isStoreB?: boolean;
}

export default function ProductCard({ product, isStoreB = false }: ProductCardProps) {
  const inStock = product.stock_qty > 0;
  const caffeine = product.attributes?.caffeine_level || "N/A";
  const flavors = product.attributes?.flavor_notes?.join(", ") || "Artisan blend";
  const origin = product.attributes?.origin || "Estate Harvest";

  return (
    <div
      className={`bg-[var(--bg-card)] border rounded-xl p-4 transition-all duration-200 hover:-translate-y-0.5 flex flex-col justify-between h-full shadow-[var(--card-shadow)] ${
        isStoreB
          ? "border-[#00baf2]/40 hover:border-[#00baf2] hover:shadow-[0_8px_24px_rgba(0,186,242,0.15)]"
          : "border-[var(--border-color)] hover:border-[#00baf2] hover:shadow-[0_8px_24px_rgba(0,186,242,0.15)]"
      }`}
    >
      <div>
        <div className="flex justify-between items-start gap-2 mb-1">
          <h3 className="font-medium text-[15px] text-[var(--text-primary)] leading-snug">
            {product.name}
          </h3>
          {inStock ? (
            <span className="bg-[var(--success-bg)] border border-[var(--success-border)] text-[var(--success-text)] text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0">
              {product.stock_qty} IN STOCK
            </span>
          ) : (
            <span className="bg-[var(--danger-bg)] border border-[var(--danger-border)] text-[var(--danger-text)] text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0">
              OUT OF STOCK
            </span>
          )}
        </div>

        <div className="font-mono text-[11px] text-[var(--text-muted)] mb-3">
          ID: <span className={isStoreB ? "text-[#00baf2]" : ""}>{product.id}</span> • {product.category}
        </div>

        <div className="text-[18px] font-semibold text-[var(--success-text)] mb-2.5">
          ₹{product.price_inr.toFixed(2)}
        </div>

        <div className="space-y-1 text-xs mb-3">
          {isStoreB && (
            <div className="text-[var(--text-secondary)]">
              Origin: <span className="text-[var(--text-primary)] font-normal">{origin}</span>
            </div>
          )}
          <div className="text-[var(--text-secondary)]">
            Caffeine: <span className="text-[var(--text-primary)] font-normal">{caffeine}</span>
          </div>
          <div className="text-[var(--text-secondary)]">
            Flavors: <span className="text-[var(--text-primary)] font-normal">{flavors}</span>
          </div>
        </div>
      </div>

      <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2 italic border-t border-[var(--border-color)]/60 pt-2">
        {product.description}
      </p>
    </div>
  );
}
