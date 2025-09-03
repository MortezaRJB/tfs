import requests
import time
import json
from datetime import datetime

class SystemMonitor:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def check_health(self):
        """Check system health"""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, {"error": str(e)}
    
    def measure_latency(self, endpoint="/"):
        """Measure response latency"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            latency = time.time() - start_time
            return latency, response.status_code
        except Exception as e:
            return None, None
    
    def run_monitoring(self, duration=60, interval=5):
        """Run monitoring for specified duration"""
        results = {
            "start_time": datetime.now().isoformat(),
            "checks": []
        }
        
        end_time = time.time() + duration
        while time.time() < end_time:
            # Health check
            health_status, health_data = self.check_health()
            
            # Latency check
            latency, status_code = self.measure_latency()
            
            check_result = {
                "timestamp": datetime.now().isoformat(),
                "health_status": health_status,
                "health_data": health_data,
                "latency": latency,
                "status_code": status_code
            }
            
            results["checks"].append(check_result)
            print(f"Health: {health_status}, Latency: {latency:.3f}s, Status: {status_code}")
            
            time.sleep(interval)
        
        return results

if __name__ == "__main__":
    monitor = SystemMonitor()
    results = monitor.run_monitoring(duration=300, interval=10)  # 5 minutes
    
    with open(f"monitoring_results_{int(time.time())}.json", "w") as f:
        json.dump(results, f, indent=2)

