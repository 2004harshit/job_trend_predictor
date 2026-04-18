import requests

BASE_URL = "http://localhost:5000/api/counselor"

def check_endpoints():
    print("--- Testing Saturation Endpoint ---")
    try:
        r1 = requests.get(f"{BASE_URL}/market-pulse/saturation", params={"days": 30})
        data1 = r1.json()
        if "indicators" in data1 and len(data1["indicators"]) > 0:
            print("Keys found in saturation indicators:", data1["indicators"][0].keys())
        else:
            print("Saturation indicators list is empty or missing.")
    except Exception as e:
        print(f"Saturation request failed: {e}")

    print("\n--- Testing Domain Comparison Endpoint ---")
    try:
        # Replace with domains you actually have in your DB
        payload = {"domains": ["Data Science", "Web Development"], "days": 60}
        r2 = requests.post(f"{BASE_URL}/domain/compare", json=payload)
        data2 = r2.json()
        if "data" in data2 and "domains" in data2["data"] and len(data2["data"]["domains"]) > 0:
            print("Keys found in domain comparison:", data2["data"]["domains"][0].keys())
            
            # Check salary structure
            first_domain = data2["data"]["domains"][0]
            print(f"Salary type: {type(first_domain.get('salary'))}")
            print(f"Salary value: {first_domain.get('salary')}")
        else:
            print("Comparison data is empty or missing.")
    except Exception as e:
        print(f"Comparison request failed: {e}")

if __name__ == "__main__":
    check_endpoints()