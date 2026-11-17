import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aliexpress_mcp.scraper import AliExpressScraper


def test_scraper():
    scraper = AliExpressScraper()

    print("=== TEST 1: RECHERCHE DE PRODUITS ===")
    res = scraper.search_products("ESP32-S3", page=1, sort="orders", free_shipping=True)
    print(f"Recherche ESP32-S3: {res.total_results} résultats trouvés")
    assert res.total_results > 0, "Aucun produit trouvé dans la recherche"
    
    first = res.products[0]
    print(f"Produit 1: {first.title[:60]}...")
    print(f"  Prix: {first.price_formatted} (numérique: {first.price_eur} EUR)")
    print(f"  Ventes: {first.sales_desc} | Note: {first.rating}")
    print(f"  Expédition: {first.shipping_tags} | Gratuit: {first.is_free_shipping}")
    print(f"  Photos: {len(first.images)} images")
    print(f"  Lien: {first.product_url}")

    test_pid = first.product_id

    print(f"\n=== TEST 2: DÉTAILS DU PRODUIT ({test_pid}) ===")
    details = scraper.get_product_details(test_pid)
    print(f"Titre: {details.title[:70]}...")
    print(f"Prix: {details.price_formatted}")
    print(f"Note: {details.rating} | Ventes: {details.sales_desc}")
    print(f"Galerie d'images: {len(details.gallery_images)} photos")

    print(f"\n=== TEST 3: AVIS CLIENTS & STATISTIQUES ({test_pid}) ===")
    reviews_res = scraper.get_product_reviews(test_pid, page=1, page_size=5, filter_type="all")
    print(f"Total avis: {reviews_res.total_reviews}")
    print(f"Note moyenne: {reviews_res.average_rating}/5.0 (Taux positif: {reviews_res.positive_percentage}%)")
    print(f"Répartition: 5★: {reviews_res.five_star_count}, 4★: {reviews_res.four_star_count}, 1★: {reviews_res.one_star_count}")
    print(f"Avis récupérés: {len(reviews_res.reviews)}")
    for i, rev in enumerate(reviews_res.reviews[:3], 1):
        print(f"  Avis {i} [{rev.buyer_country}] - Note: {rev.stars}/5 - Date: {rev.date}")
        if rev.feedback:
            clean_fb = rev.feedback.replace('\n', ' ')[:90]
            print(f"    Commentaire: {clean_fb}...")
        if rev.images:
            print(f"    Photos client: {len(rev.images)} images")

    print("\n TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")


if __name__ == "__main__":
    test_scraper()
