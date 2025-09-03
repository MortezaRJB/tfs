import requests
import threading
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor

class LoadTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "upload_times": [],
            "download_times": [],
            "errors": []
        }
    
    def create_test_file(self, size_kb=100):
        """Create a test file of specified size"""
        content = "A" * (size_kb * 1024)
        filename = f"test_file_{random.randint(1000, 9999)}.txt"
        with open(filename, "w") as f:
            f.write(content)
        return filename
    
    def upload_file(self, thread_id):
        """Upload a test file"""
        try:
            filename = self.create_test_file(random.randint(50, 500))  # 50-500KB
            
            start_time = time.time()
            with open(filename, "rb") as f:
                files = {"file": f}
                data = {
                    "expiry_minutes": random.choice([5, 30, 60, 360]),
                    "max_downloads": random.randint(10, 100)
                }
                response = requests.post(f"{self.base_url}/", files=files, data=data, timeout=30)
            
            upload_time = time.time() - start_time
            
            # Clean up test file
            os.remove(filename)
            
            if response.status_code in [200, 302]:
                self.results["upload_times"].append(upload_time)
                print(f"Thread {thread_id}: Upload successful in {upload_time:.2f}s")
                return True
            else:
                self.results["errors"].append(f"Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.results["errors"].append(f"Upload error: {str(e)}")
            return False
    
    def download_test(self, token):
        """Test file download"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/download/{token}/", timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                self.results["download_times"].append(download_time)
                return True
            else:
                self.results["errors"].append(f"Download failed: {response.status_code}")
                return False
        except Exception as e:
            self.results["errors"].append(f"Download error: {str(e)}")
            return False
    
    def run_load_test(self, num_threads=10, requests_per_thread=5):
        """Run load test with multiple threads"""
        print(f"Starting load test: {num_threads} threads, {requests_per_thread} requests each")
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                for j in range(requests_per_thread):
                    future = executor.submit(self.upload_file, f"{i}-{j}")
                    futures.append(future)
            
            # Wait for all uploads to complete
            for future in futures:
                future.result()
        
        # Calculate statistics
        if self.results["upload_times"]:
            avg_upload = sum(self.results["upload_times"]) / len(self.results["upload_times"])
            max_upload = max(self.results["upload_times"])
            min_upload = min(self.results["upload_times"])
            
            print(f"\nUpload Statistics:")
            print(f"Total uploads: {len(self.results['upload_times'])}")
            print(f"Average time: {avg_upload:.2f}s")
            print(f"Max time: {max_upload:.2f}s")
            print(f"Min time: {min_upload:.2f}s")
        
        if self.results["errors"]:
            print(f"\nErrors: {len(self.results['errors'])}")
            for error in self.results["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")

if __name__ == "__main__":
    tester = LoadTester()
    tester.run_load_test(num_threads=20, requests_per_thread=3)

