import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aliexpress_mcp.scraper import AliExpressScraper

queries = [
    "esp32",
    "raspberry pi",
    "arduino uno",
    "cle usb 128go",
    "carte micro sd",
    "imprimante 3d",
    "chargeur gan 65w",
    "tournevis precision",
    "multimetre numerique",
    "fer a souder ts101",
    "ruban led ws2812b",
    "montre connectee",
    "ecouteurs sans fil bluetooth",
    "power bank 20000mah",
    "camera esp32 cam",
]

def run_stress_test():
    scraper = AliExpressScraper()
    print(f"=== TEST D'ENDURANCE : {len(queries)} RECHERCHES CONSÉCUTIVES ===")
    
    success_count = 0
    fail_count = 0
    times = []
    product_ids_found = []

    for i, q in enumerate(queries, 1):
        t0 = time.time()
        try:
            res = scraper.search_products(q, page=1, sort="orders")
            elapsed = time.time() - t0
            times.append(elapsed)
            
            if res.total_results > 0:
                success_count += 1
                first = res.products[0]
                product_ids_found.append(first.product_id)
                print(f"[{i}/{len(queries)}] '{q}' -> OK ({res.total_results} items, {elapsed:.2f}s) | 1er: {first.title[:45]}... ({first.price_formatted})")
            else:
                fail_count += 1
                print(f"[{i}/{len(queries)}] '{q}' -> VIDE / AUCUN RÉSULTAT ({elapsed:.2f}s)")
        except Exception as e:
            fail_count += 1
            elapsed = time.time() - t0
            print(f"[{i}/{len(queries)}] '{q}' -> ERREUR ({elapsed:.2f}s): {e}")

        # Pas de long sommeil : test rapide d'affilée (0.2s - 0.5s)
        time.sleep(0.3)

    print("\n=== TEST DES FICHES DÉTAILS ET AVIS D'AFFILÉE ===")
    details_ok = 0
    reviews_ok = 0

    for i, pid in enumerate(product_ids_found[:8], 1):
        t0 = time.time()
        try:
            d = scraper.get_product_details(pid)
            d_time = time.time() - t0
            print(f"[Détail {i}/8] ID {pid} -> OK ({d_time:.2f}s) | Titre: {d.title[:45]}... | Prix: {d.price_formatted} | Note: {d.rating}")
            details_ok += 1
        except Exception as e:
            print(f"[Détail {i}/8] ID {pid} -> ERREUR: {e}")

        time.sleep(0.3)

        t1 = time.time()
        try:
            r = scraper.get_product_reviews(pid, page=1, page_size=5)
            r_time = time.time() - t1
            print(f"[Avis {i}/8] ID {pid} -> OK ({r_time:.2f}s) | Total: {r.total_reviews} avis | Moyenne: {r.average_rating}/5 | {len(r.reviews)} avis lus")
            reviews_ok += 1
        except Exception as e:
            print(f"[Avis {i}/8] ID {pid} -> ERREUR: {e}")

        time.sleep(0.3)

    print("\n=== BILAN DU TEST D'AFFILÉE ===")
    print(f"Recherches : {success_count}/{len(queries)} réussies ({success_count/len(queries)*100:.1f}%)")
    print(f"Fiches détails : {details_ok}/8 réussies ({details_ok/8*100:.1f}%)")
    print(f"Avis clients : {reviews_ok}/8 réussis ({reviews_ok/8*100:.1f}%)")
    if times:
        print(f"Temps moyen par recherche : {sum(times)/len(times):.2f}s")


if __name__ == "__main__":
    run_stress_test()
