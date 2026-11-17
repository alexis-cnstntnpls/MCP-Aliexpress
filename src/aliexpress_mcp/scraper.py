import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from curl_cffi import requests

from .models import (
    ProductDetail,
    ProductReview,
    ProductReviewResponse,
    ProductSearchResponse,
    ProductSearchResult,
)

logger = logging.getLogger("aliexpress_mcp")
logger.setLevel(logging.INFO)


class AliExpressScraper:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session(impersonate="chrome124")
        # Cookie pour forcer la région France, langue française et devise EUR
        self.session.cookies.set(
            "aep_usuc_f",
            "region=FR&b_locale=fr_FR&site=fra&c_tp=EUR",
            domain=".aliexpress.com",
        )
        self.base_headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def _extract_item_list(self, html: str) -> List[Dict[str, Any]]:
        """Extrait le tableau JSON itemList.content du HTML de recherche wholesale."""
        idx = html.find('"itemList":')
        if idx == -1:
            return []

        c_idx = html.find('"content":', idx)
        if c_idx == -1:
            return []

        b_idx = html.find("[", c_idx)
        if b_idx == -1:
            return []

        depth = 0
        end_idx = b_idx
        for i in range(b_idx, len(html)):
            char = html[i]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break

        if depth != 0:
            return []

        try:
            items_raw = json.loads(html[b_idx:end_idx])
            return items_raw if isinstance(items_raw, list) else []
        except Exception as e:
            logger.warning(f"Erreur décodage JSON itemList: {e}")
            return []

    def _format_image_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        if url.startswith("//"):
            return f"https:{url}"
        return url

    def search_products(
        self,
        query: str,
        page: int = 1,
        sort: str = "default",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        free_shipping: bool = False,
    ) -> ProductSearchResponse:
        """
        Recherche des produits sur AliExpress FR.
        :param query: Termes de recherche
        :param page: Numéro de page (1 par défaut)
        :param sort: 'default', 'price_asc', 'price_desc', 'orders'
        :param min_price: Prix minimum en EUR
        :param max_price: Prix maximum en EUR
        :param free_shipping: Filtrer uniquement livraison gratuite
        """
        clean_kw = "-".join(re.sub(r"[^\w\s-]", "", query).split())
        if not clean_kw:
            clean_kw = quote(query)

        url = f"https://fr.aliexpress.com/w/wholesale-{clean_kw}.html"
        params: Dict[str, Any] = {"page": page}

        if sort == "price_asc":
            params["sortType"] = "price_asc"
        elif sort == "price_desc":
            params["sortType"] = "price_desc"
        elif sort in ("orders", "sales"):
            params["sortType"] = "total_tranpro_desc"

        if min_price is not None:
            params["minPrice"] = min_price
        if max_price is not None:
            params["maxPrice"] = max_price

        if free_shipping:
            params["isFreeShip"] = "y"

        resp = self.session.get(
            url,
            params=params,
            headers=self.base_headers,
            timeout=self.timeout,
        )

        if resp.status_code != 200:
            logger.error(f"Échec recherche wholesale HTTP {resp.status_code}")
            return ProductSearchResponse(
                query=query, page=page, total_results=0, products=[]
            )

        items_raw = self._extract_item_list(resp.text)
        products: List[ProductSearchResult] = []

        for item in items_raw:
            pid = str(item.get("productId") or "")
            if not pid:
                continue

            title = item.get("title", {}).get("displayTitle") or "Article sans titre"

            # Prix
            prices_data = item.get("prices", {})
            sale_price = prices_data.get("salePrice", {})
            formatted_price = sale_price.get("formattedPrice") or "N/A"
            min_price_num = sale_price.get("minPrice")
            discount = sale_price.get("discount")

            ut_map = item.get("trace", {}).get("utLogMap", {})
            origin_price_raw = ut_map.get("originPriceAmount")
            origin_price_eur = None
            if origin_price_raw:
                try:
                    origin_price_eur = float(origin_price_raw) / 100.0
                except (ValueError, TypeError):
                    pass

            # Ventes & notes
            trade_desc = item.get("trade", {}).get("tradeDesc")
            evaluation = item.get("evaluation", {})
            star_rating = evaluation.get("starRating")
            if star_rating is not None:
                try:
                    star_rating = float(star_rating)
                except (ValueError, TypeError):
                    star_rating = None

            # Badges livraison
            shipping_tags = []
            is_free = False
            for sp in item.get("sellingPoints", []):
                tag_content = sp.get("tagContent", {})
                tag_text = tag_content.get("tagText")
                if tag_text:
                    shipping_tags.append(tag_text)
                    if "gratuit" in tag_text.lower():
                        is_free = True

            ship_from = item.get("trace", {}).get("pdpParams", {}).get("shipFrom")

            # Images
            primary_img = self._format_image_url(
                item.get("image", {}).get("imgUrl")
            )
            gallery = []
            for img_obj in item.get("images", []):
                img_u = self._format_image_url(img_obj.get("imgUrl"))
                if img_u and img_u not in gallery:
                    gallery.append(img_u)

            if not primary_img and gallery:
                primary_img = gallery[0]

            product_url = f"https://fr.aliexpress.com/item/{pid}.html"

            products.append(
                ProductSearchResult(
                    product_id=pid,
                    title=title,
                    price_formatted=formatted_price,
                    price_eur=float(min_price_num) if min_price_num is not None else None,
                    original_price_eur=origin_price_eur,
                    discount_percent=int(discount) if discount is not None else None,
                    sales_desc=trade_desc,
                    rating=star_rating,
                    shipping_tags=shipping_tags,
                    is_free_shipping=is_free,
                    ship_from=ship_from,
                    image_url=primary_img,
                    images=gallery,
                    product_url=product_url,
                )
            )

        return ProductSearchResponse(
            query=query,
            page=page,
            total_results=len(products),
            products=products,
        )

    def get_product_details(self, product_id_or_url: str) -> ProductDetail:
        """
        Récupère les détails d'un produit AliExpress FR.
        :param product_id_or_url: ID numérique ou URL complète de l'article
        """
        id_match = re.search(r"(\d{10,20})", product_id_or_url)
        if not id_match:
            raise ValueError(f"Impossible d'extraire l'ID produit de: {product_id_or_url}")

        pid = id_match.group(1)
        url = f"https://fr.aliexpress.com/item/{pid}.html"

        resp = self.session.get(url, headers=self.base_headers, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Échec accès produit {pid} (HTTP {resp.status_code})")

        # Extraction métadonnées HTML
        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', resp.text)
        title = title_match.group(1) if title_match else f"Article {pid}"

        image_match = re.search(r'<meta property="og:image" content="([^"]+)"', resp.text)
        cover_image = self._format_image_url(image_match.group(1) if image_match else None)

        gallery = []
        dc_match = re.search(r"window\._d_c_\.DCData\s*=\s*(\{.+?\});", resp.text, re.DOTALL)
        if dc_match:
            try:
                dc_data = json.loads(dc_match.group(1))
                for img_url in dc_data.get("imagePathList", []):
                    f_url = self._format_image_url(img_url)
                    if f_url and f_url not in gallery:
                        gallery.append(f_url)
            except Exception:
                pass

        if not gallery and cover_image:
            gallery.append(cover_image)

        # Recherche correspondante pour récupérer prix, notation et expédition
        price_formatted = None
        price_eur = None
        original_price_eur = None
        discount_percent = None
        sales_desc = None
        rating = None
        shipping_tags = []

        # Récupération fiable de la note moyenne via l'API feedback
        try:
            rev_res = self.get_product_reviews(pid, page=1, page_size=1)
            if rev_res.average_rating is not None:
                rating = rev_res.average_rating
        except Exception as e:
            logger.debug(f"Note non disponible via feedback: {e}")

        # On extrait les termes les plus pertinents du titre (mots alphanumériques / modèles)
        words = [w for w in re.sub(r"[^\w\s-]", " ", title).split() if len(w) >= 3]
        # Essayer d'abord avec les 2 premiers mots pertinents
        search_candidates = []
        if len(words) >= 2:
            search_candidates.append(" ".join(words[:2]))
        if len(words) >= 3:
            search_candidates.append(" ".join(words[:3]))
        if not search_candidates:
            search_candidates.append(title[:30])

        for cand in search_candidates:
            try:
                search_res = self.search_products(cand, page=1)
                matched = next((p for p in search_res.products if p.product_id == pid), None)
                if not matched:
                    # Tenter avec tri par ventes
                    search_res_orders = self.search_products(cand, page=1, sort="orders")
                    matched = next((p for p in search_res_orders.products if p.product_id == pid), None)

                if matched:
                    price_formatted = matched.price_formatted
                    price_eur = matched.price_eur
                    original_price_eur = matched.original_price_eur
                    discount_percent = matched.discount_percent
                    if matched.sales_desc:
                        sales_desc = matched.sales_desc
                    if rating is None and matched.rating is not None:
                        rating = matched.rating
                    shipping_tags = matched.shipping_tags
                    if not gallery and matched.images:
                        gallery = matched.images
                    break
            except Exception as e:
                logger.debug(f"Erreur tentative recherche candidate '{cand}': {e}")

        return ProductDetail(
            product_id=pid,
            title=title,
            price_formatted=price_formatted,
            price_eur=price_eur,
            original_price_eur=original_price_eur,
            discount_percent=discount_percent,
            sales_desc=sales_desc,
            rating=rating,
            shipping_tags=shipping_tags,
            image_url=cover_image or (gallery[0] if gallery else None),
            gallery_images=gallery,
            product_url=url,
        )

    def get_product_reviews(
        self,
        product_id_or_url: str,
        page: int = 1,
        page_size: int = 10,
        filter_type: str = "all",
    ) -> ProductReviewResponse:
        """
        Récupère les avis clients vérifiés et statistiques d'évaluation pour un produit.
        :param product_id_or_url: ID numérique ou URL de l'article
        :param page: Numéro de page
        :param page_size: Nombre d'avis par page (max 20)
        :param filter_type: 'all', 'local' (France/local), 'image' (avec photos)
        """
        id_match = re.search(r"(\d{10,20})", product_id_or_url)
        if not id_match:
            raise ValueError(f"Impossible d'extraire l'ID produit de: {product_id_or_url}")

        pid = id_match.group(1)
        url = "https://feedback.aliexpress.com/pc/searchEvaluation.do"
        params = {
            "productId": pid,
            "page": page,
            "pageSize": min(page_size, 20),
            "filter": filter_type if filter_type in ("all", "local", "image") else "all",
        }

        resp = self.session.get(url, params=params, headers=self.base_headers, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Échec récupération avis (HTTP {resp.status_code})")

        data = resp.json().get("data", {})
        stat = data.get("productEvaluationStatistic", {})

        total_reviews = data.get("totalNum", 0)
        total_pages = data.get("totalPage", 0)
        avg_star = stat.get("evarageStar")
        pos_rate = stat.get("positiveRate")

        reviews_list: List[ProductReview] = []
        for eva in data.get("evaViewList", []):
            buyer_eval = eva.get("buyerEval")  # ex: 100, 80, 60...
            stars = (float(buyer_eval) / 20.0) if buyer_eval is not None else None

            rev_imgs = [
                self._format_image_url(u) for u in eva.get("images", []) if u
            ]

            reviews_list.append(
                ProductReview(
                    review_id=str(eva.get("evaluationIdStr") or eva.get("evaluationId") or ""),
                    buyer_name=eva.get("buyerName"),
                    buyer_country=eva.get("buyerCountry"),
                    rating=buyer_eval,
                    stars=stars,
                    date=eva.get("evalDate"),
                    feedback=eva.get("buyerFeedback"),
                    variant_info=eva.get("skuInfo"),
                    logistics=eva.get("logistics"),
                    images=[img for img in rev_imgs if img],
                )
            )

        return ProductReviewResponse(
            product_id=pid,
            page=page,
            page_size=params["pageSize"],
            total_reviews=total_reviews,
            total_pages=total_pages,
            average_rating=float(avg_star) if avg_star is not None else None,
            positive_percentage=float(pos_rate) if pos_rate is not None else None,
            five_star_count=stat.get("fiveStarNum"),
            four_star_count=stat.get("fourStarNum"),
            three_star_count=stat.get("threeStarNum"),
            two_star_count=stat.get("twoStarNum"),
            one_star_count=stat.get("oneStarNum"),
            reviews=reviews_list,
        )
