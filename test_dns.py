import subprocess
import time
import socket

def test_dns():
    # Start the proxy in the background
    process = subprocess.Popen(
        ["../venv/bin/python3", "main.py"],
        cwd="app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(5) # Wait for it to start
    
    try:
        # Test allowed domain
        print("Testing google.com (should be allowed)...")
        result = subprocess.run(
            ["dig", "@127.0.0.1", "-p", "5353", "google.com", "+short"],
            capture_output=True, text=True
        )
        output = result.stdout.strip()
        print(f"Result: {output}")
        if output and not "communications error" in output:
            print("PASS: google.com resolved.")
        else:
            print("FAIL: google.com did not resolve.")

        # Test blocked domain
        print("\nTesting example.com (should be blocked)...")
        result = subprocess.run(
            ["dig", "@127.0.0.1", "-p", "5353", "example.com"],
            capture_output=True, text=True
        )
        if "status: NXDOMAIN" in result.stdout:
            print("PASS: example.com blocked with NXDOMAIN.")
        else:
            print(f"FAIL: example.com was not blocked correctly. Status: {result.stdout}")

        # Test Dashboard API
        print("\nTesting Dashboard API...")
        try:
            import requests
            response = requests.get("http://127.0.0.1:8080/api/stats", timeout=5)
            if response.status_code == 200:
                print(f"PASS: Stats API responded: {response.json()}")
            else:
                print(f"FAIL: Stats API status code: {response.status_code}")
            
            # Test Adding Rule via API
            print("Testing Adding Rule via API...")
            res = requests.post("http://127.0.0.1:8080/api/rules/add", json={"rule": "api-blocked.com"})
            if res.status_code == 200:
                print("PASS: Rule added via API.")
            
            # Verify the rule is active
            print("Verifying API-added rule...")
            result = subprocess.run(
                ["dig", "@127.0.0.1", "-p", "5353", "api-blocked.com"],
                capture_output=True, text=True
            )
            if "status: NXDOMAIN" in result.stdout:
                print("PASS: API-added rule is working.")
            else:
                print("FAIL: API-added rule is NOT working.")

        except Exception as e:
            print(f"FAIL: Dashboard API error: {e}")

    finally:
        process.terminate()
        stdout, stderr = process.communicate()
        print("\nProxy Output:")
        print(stdout)
        if stderr:
            print("Proxy Error:")
            print(stderr)

if __name__ == "__main__":
    test_dns()
