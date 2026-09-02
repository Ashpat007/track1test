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
      className={`bg-[#11131c]/75 border rounded-xl p-4 backdrop-blur-md transition-all duration-200 hover:-translate-y-0.5 flex flex-col justify-between h-full ${
        isStoreB
          ? "border-[#00baf2]/30 hover:border-[#00baf2] hover:shadow-[0_8px_24px_rgba(0,186,242,0.15)]"
          : "border-[#1e2230] hover:border-[#00baf2] hover:shadow-[0_8px_24px_rgba(0,186,242,0.15)]"
      }`}
    >
      <div>
        <div className="flex justify-between items-start gap-2 mb-1">
          <h3 className="font-medium text-[15px] text-[#f4f4f5] leading-snug">
            {product.name}
          </h3>
          {inStock ? (
            <span className="bg-[#10b981]/10 border border-[#10b981]/25 text-[#10b981] text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0">
              {product.stock_qty} IN STOCK
            </span>
          ) : (
            <span className="bg-[#ef4444]/10 border border-[#ef4444]/25 text-[#ef4444] text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0">
              OUT OF STOCK
            </span>
          )}
        </div>

        <div className="font-mono text-[11px] text-[#64748b] mb-3">
          ID: <span className={isStoreB ? "text-[#00baf2]" : ""}>{product.id}</span> • {product.category}
        </div>

        <div className="text-[18px] font-semibold text-[#10b981] mb-2.5">
          ₹{product.price_inr.toFixed(2)}
        </div>

        <div className="space-y-1 text-xs mb-3">
          {isStoreB && (
            <div className="text-[#71717a]">
              Origin: <span className="text-[#d4d4d8] font-normal">{origin}</span>
            </div>
          )}
          <div className="text-[#71717a]">
            Caffeine: <span className="text-[#d4d4d8] font-normal">{caffeine}</span>
          </div>
          <div className="text-[#71717a]">
            Flavors: <span className="text-[#d4d4d8] font-normal">{flavors}</span>
          </div>
        </div>
      </div>

      <p className="text-[11px] text-[#71717a] line-clamp-2 italic border-t border-[#1e2230]/60 pt-2">
        {product.description}
      </p>
    </div>
  );
}
