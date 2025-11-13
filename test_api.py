import httpx
import json

API_URL = "https://sales-angel-production-production.up.railway.app"

def test_enrichment():
    # Test single enrichment
    response = httpx.post(
        f"{API_URL}/api/enrichment/enrich",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "company": "Test Corp"
        }
    )
    print("Single Enrichment:", json.dumps(response.json(), indent=2))
    
    # Test bulk enrichment
    response = httpx.post(
        f"{API_URL}/api/enrichment/bulk-enrich",
        json=[
            {"email": "lead1@example.com", "name": "Lead One"},
            {"email": "lead2@example.com", "name": "Lead Two"},
            {"email": "lead3@example.com", "name": "Lead Three"}
        ]
    )
    print("\nBulk Enrichment:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_enrichment()
