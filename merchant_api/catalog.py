"""
Structured product catalog for Aura Artisan Teas & Botanical Blends.
Demonstrates agent-readable attributes: category, variants, price in INR, tags, stock level, semantic specifications, and visual product URLs.
"""

INITIAL_CATALOG = [
    {
        "id": "tea-001",
        "name": "Kashmir Kahwa Saffron Blend",
        "category": "Green Tea",
        "price_inr": 420.0,
        "stock_qty": 15,
        "description": "Artisanal Kashmiri Kahwa blended with green tea leaves, real saffron strands, cardamom, and sliced almonds.",
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80",
        "tags": ["kahwa", "saffron", "warming", "spiced", "kashmir", "medium-caffeine"],
        "attributes": {
            "caffeine_level": "Medium",
            "flavor_notes": ["Spiced", "Nutty", "Sweet Saffron"],
            "origin": "Kashmir, India"
        },
        "variants": [
            {"id": "v-100g", "name": "100g Loose Leaf Pouch", "price_modifier_inr": 0.0, "stock_qty": 10},
            {"id": "v-250g", "name": "250g Tin Can", "price_modifier_inr": 350.0, "stock_qty": 5}
        ]
    },
    {
        "id": "tea-002",
        "name": "Himalayan Chamomile Lavender Infusion",
        "category": "Herbal Infusion",
        "price_inr": 380.0,
        "stock_qty": 20,
        "description": "Calming caffeine-free herbal tea with whole Himalayan chamomile flowers and organic French lavender buds.",
        "image_url": "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?auto=format&fit=crop&w=600&q=80",
        "tags": ["herbal", "caffeine-free", "sleep", "calming", "floral", "lavender"],
        "attributes": {
            "caffeine_level": "None",
            "flavor_notes": ["Floral", "Honey", "Soothing Lavender"],
            "origin": "Himachal Pradesh, India"
        },
        "variants": [
            {"id": "v-75g", "name": "75g Jar", "price_modifier_inr": 0.0, "stock_qty": 12},
            {"id": "v-20pyramids", "name": "20 Pyramid Tea Bags Box", "price_modifier_inr": 70.0, "stock_qty": 8}
        ]
    },
    {
        "id": "tea-003",
        "name": "Imperial Darjeeling First Flush",
        "category": "Black Tea",
        "price_inr": 650.0,
        "stock_qty": 8,
        "description": "The Champagne of teas. Delicate first flush spring harvest from high-altitude Darjeeling estates with muscatel notes.",
        "image_url": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=600&q=80",
        "tags": ["darjeeling", "black tea", "first flush", "muscatel", "premium", "high-caffeine"],
        "attributes": {
            "caffeine_level": "High",
            "flavor_notes": ["Muscatel Grape", "Floral", "Crisp Finish"],
            "origin": "Darjeeling, West Bengal"
        },
        "variants": [
            {"id": "v-100g-tin", "name": "100g Collector's Tin", "price_modifier_inr": 0.0, "stock_qty": 8}
        ]
    },
    {
        "id": "tea-004",
        "name": "Masala Chai Reserve (Whole Spices)",
        "category": "Black Tea",
        "price_inr": 290.0,
        "stock_qty": 25,
        "description": "Robust Assam CTC tea blended with crushed Kerala green cardamom, cinnamon, cloves, ginger, and black pepper.",
        "image_url": "https://images.unsplash.com/photo-1561336313-0bd5e0b27ec8?auto=format&fit=crop&w=600&q=80",
        "tags": ["masala chai", "assam", "spiced", "bold", "strong", "high-caffeine"],
        "attributes": {
            "caffeine_level": "High",
            "flavor_notes": ["Pungent Spice", "Rich Malt", "Peppery"],
            "origin": "Assam & Kerala, India"
        },
        "variants": [
            {"id": "v-200g", "name": "200g Pack", "price_modifier_inr": 0.0, "stock_qty": 20},
            {"id": "v-500g", "name": "500g Value Pack", "price_modifier_inr": 240.0, "stock_qty": 5}
        ]
    },
    {
        "id": "tea-005",
        "name": "Organic Japanese Matcha Grade-A",
        "category": "Matcha",
        "price_inr": 950.0,
        "stock_qty": 3,
        "description": "Shade-grown stone-ground ceremonial grade green tea powder rich in L-theanine and antioxidants.",
        "image_url": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=600&q=80",
        "tags": ["matcha", "ceremonial", "superfood", "green tea", "premium", "clean-energy"],
        "attributes": {
            "caffeine_level": "Medium-High",
            "flavor_notes": ["Umami", "Vegetal", "Smooth"],
            "origin": "Uji, Japan"
        },
        "variants": [
            {"id": "v-50g-tin", "name": "50g Sealed Tin", "price_modifier_inr": 0.0, "stock_qty": 3}
        ]
    },
    {
        "id": "tea-006",
        "name": "Tulsi Ginger Detox Infusion",
        "category": "Herbal Infusion",
        "price_inr": 320.0,
        "stock_qty": 18,
        "description": "Holy basil blend with crushed sun-dried ginger roots and lemongrass.",
        "image_url": "https://images.unsplash.com/photo-1514733670139-4d87a1941d55?auto=format&fit=crop&w=600&q=80",
        "tags": ["tulsi", "ginger", "detox", "caffeine-free", "immunity"],
        "attributes": {
            "caffeine_level": "None",
            "flavor_notes": ["Zesty Ginger", "Herbal Basil"],
            "origin": "Uttarakhand, India"
        },
        "variants": [
            {"id": "v-100g-pack", "name": "100g Pack", "price_modifier_inr": 0.0, "stock_qty": 18}
        ]
    },
    {
        "id": "tea-007",
        "name": "Kashmiri Pure Saffron Strands",
        "category": "Spices",
        "price_inr": 750.0,
        "stock_qty": 10,
        "description": "100% pure Grade-A Mongra Kashmiri saffron strands harvested in Pampore.",
        "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=600&q=80",
        "tags": ["saffron", "spice", "mongra", "kashmir", "luxury"],
        "attributes": {
            "caffeine_level": "None",
            "flavor_notes": ["Aromatic Saffron", "Rich Color"],
            "origin": "Pampore, Kashmir"
        },
        "variants": [
            {"id": "v-1g-jar", "name": "1g Sealed Glass Jar", "price_modifier_inr": 0.0, "stock_qty": 10}
        ]
    },
    {
        "id": "tea-008",
        "name": "Royal Earl Grey Bergamot",
        "category": "Black Tea",
        "price_inr": 480.0,
        "stock_qty": 14,
        "description": "Single-estate Nilgiri black tea infused with natural Italian bergamot citrus oil.",
        "image_url": "https://images.unsplash.com/photo-1594631252845-29fc4cc86de5?auto=format&fit=crop&w=600&q=80",
        "tags": ["earl grey", "bergamot", "citrus", "black tea", "classic"],
        "attributes": {
            "caffeine_level": "High",
            "flavor_notes": ["Citrus Bergamot", "Smooth Black Tea"],
            "origin": "Nilgiris, Tamil Nadu"
        },
        "variants": [
            {"id": "v-150g-tin", "name": "150g Tin", "price_modifier_inr": 0.0, "stock_qty": 14}
        ]
    }
]
