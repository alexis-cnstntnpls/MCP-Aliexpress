from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ProductSearchResult(BaseModel):
    product_id: str = Field(..., description="Identifiant unique du produit AliExpress")
    title: str = Field(..., description="Titre complet du produit en français")
    price_formatted: str = Field(..., description="Prix formaté affiché (ex: '€ 12,50')")
    price_eur: Optional[float] = Field(None, description="Prix numérique en euros")
    original_price_eur: Optional[float] = Field(None, description="Prix initial avant réduction en euros")
    discount_percent: Optional[int] = Field(None, description="Pourcentage de réduction appliqué")
    sales_desc: Optional[str] = Field(None, description="Volume des ventes (ex: '+ 5 000 vendus')")
    rating: Optional[float] = Field(None, description="Note moyenne sur 5 étoiles")
    shipping_tags: List[str] = Field(default_factory=list, description="Badges et conditions de livraison")
    is_free_shipping: bool = Field(False, description="Indique si la livraison est gratuite")
    ship_from: Optional[str] = Field(None, description="Pays d'expédition si disponible (ex: 'FR', 'ES', 'CN')")
    image_url: Optional[str] = Field(None, description="URL de la photo principale")
    images: List[str] = Field(default_factory=list, description="Liste d'URLs d'images du produit")
    product_url: str = Field(..., description="Lien direct vers la fiche produit AliExpress FR")


class ProductSearchResponse(BaseModel):
    query: str
    page: int
    total_results: int
    products: List[ProductSearchResult]


class ProductDetail(BaseModel):
    product_id: str
    title: str
    price_formatted: Optional[str] = None
    price_eur: Optional[float] = None
    original_price_eur: Optional[float] = None
    discount_percent: Optional[int] = None
    sales_desc: Optional[str] = None
    rating: Optional[float] = None
    shipping_tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    gallery_images: List[str] = Field(default_factory=list)
    product_url: str


class ProductReview(BaseModel):
    review_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_country: Optional[str] = None
    rating: Optional[int] = Field(None, description="Note attribuée (ex: 100 pour 5 étoiles)")
    stars: Optional[float] = Field(None, description="Note convertie sur 5 étoiles")
    date: Optional[str] = None
    feedback: Optional[str] = None
    variant_info: Optional[str] = None
    logistics: Optional[str] = None
    images: List[str] = Field(default_factory=list)


class ProductReviewResponse(BaseModel):
    product_id: str
    page: int
    page_size: int
    total_reviews: int
    total_pages: int
    average_rating: Optional[float] = None
    positive_percentage: Optional[float] = None
    five_star_count: Optional[int] = None
    four_star_count: Optional[int] = None
    three_star_count: Optional[int] = None
    two_star_count: Optional[int] = None
    one_star_count: Optional[int] = None
    reviews: List[ProductReview]
