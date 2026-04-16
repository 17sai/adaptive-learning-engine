#!/usr/bin/env python3
"""
Load Testing Script for Adaptive Learning System
Simulates realistic student activity to verify production readiness
Usage: python load_test.py --students 100 --duration 300
"""

import requests
import time
import random
import argparse
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

class LoadTestRunner:
    def __init__(self, api_url="http://localhost:8000", num_students=10, duration=60):
        self.api_url = api_url
        self.num_students = num_students
        self.duration = duration
        self.session = requests.Session()
        self.results = {
            "recommendations": [],
            "assessments": [],
            "errors": []
        }
        self.student_ids = []
        
    def setup(self):
        """Register test students"""
        print(f"📝 Registering {self.num_students} test students...")
        for i in range(self.num_students):
            try:
                response = self.session.post(
                    f"{self.api_url}/api/admin/students",
                    json={
                        "email": f"loadtest{i}@school.edu",
                        "full_name": f"Load Test Student {i}",
                        "cohort_id": 1 if i % 2 == 0 else 2,
                        "grade_level": 9 + (i % 4)
                    }
                )
                if response.status_code == 200:
                    student_id = response.json()["student_id"]
                    self.student_ids.append(student_id)
            except Exception as e:
                self.results["errors"].append(f"Setup error: {e}")
        
        print(f"✅ Registered {len(self.student_ids)} students")
        return len(self.student_ids) > 0
    
    def get_recommendation(self, student_id):
        """Simulate a student requesting a recommendation"""
        start = time.time()
        try:
            response = self.session.get(
                f"{self.api_url}/api/students/{student_id}/recommendation"
            )
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                self.results["recommendations"].append({
                    "status": "success",
                    "response_time_ms": elapsed
                })
            else:
                self.results["errors"].append(f"Recommendation failed: {response.status_code}")
        except Exception as e:
            self.results["errors"].append(f"Recommendation error: {e}")
    
    def submit_assessment(self, student_id):
        """Simulate a student submitting an assessment"""
        start = time.time()
        try:
            # Pick random topic and score
            topic_id = random.randint(1, 5)
            score = random.uniform(50, 100)  # 50-100 percent
            
            response = self.session.post(
                f"{self.api_url}/api/students/{student_id}/assessment-result",
                json={
                    "topic_id": topic_id,
                    "score": score,
                    "num_questions": 20,
                    "time_spent_seconds": random.randint(300, 1800)
                }
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                self.results["assessments"].append({
                    "status": "success",
                    "response_time_ms": elapsed
                })
            else:
                self.results["errors"].append(f"Assessment failed: {response.status_code}")
        except Exception as e:
            self.results["errors"].append(f"Assessment error: {e}")
    
    def run_load_test(self):
        """Run the load test"""
        if not self.student_ids:
            print("❌ No students registered. Cannot run load test.")
            return False
        
        print(f"\n🚀 Starting load test ({self.num_students} students, {self.duration}s duration)")
        print("This simulates students requesting recommendations and submitting assessments...\n")
        
        start_time = time.time()
        request_count = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            while time.time() - start_time < self.duration:
                # Randomly pick an action and student
                action = random.choice(["recommendation", "assessment"])
                student_id = random.choice(self.student_ids)
                
                if action == "recommendation":
                    future = executor.submit(self.get_recommendation, student_id)
                else:
                    future = executor.submit(self.submit_assessment, student_id)
                
                futures.append(future)
                request_count += 1
                
                # Small delay between submitting tasks
                time.sleep(0.05)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                future.result()
        
        elapsed = time.time() - start_time
        print(f"✅ Load test completed in {elapsed:.1f} seconds")
        print(f"📊 Total requests: {request_count}\n")
        
        return True
    
    def print_results(self):
        """Print load test results"""
        print("="*70)
        print("LOAD TEST RESULTS".center(70))
        print("="*70 + "\n")
        
        total_requests = len(self.results["recommendations"]) + len(self.results["assessments"])
        total_errors = len(self.results["errors"])
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests else 0
        
        print(f"📊 SUMMARY:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful: {total_requests - total_errors}")
        print(f"   Failed: {total_errors}")
        print(f"   Success Rate: {success_rate:.1f}%\n")
        
        # Recommendation metrics
        if self.results["recommendations"]:
            rec_times = [r["response_time_ms"] for r in self.results["recommendations"]]
            print(f"🎯 RECOMMENDATIONS ({len(rec_times)} requests):")
            print(f"   Min: {min(rec_times):.2f} ms")
            print(f"   Max: {max(rec_times):.2f} ms")
            print(f"   Avg: {statistics.mean(rec_times):.2f} ms")
            print(f"   Median: {statistics.median(rec_times):.2f} ms")
            print(f"   P95: {sorted(rec_times)[int(len(rec_times)*0.95)]:.2f} ms")
            print(f"   P99: {sorted(rec_times)[int(len(rec_times)*0.99)]:.2f} ms\n")
        
        # Assessment metrics
        if self.results["assessments"]:
            assess_times = [a["response_time_ms"] for a in self.results["assessments"]]
            print(f"📝 ASSESSMENTS ({len(assess_times)} requests):")
            print(f"   Min: {min(assess_times):.2f} ms")
            print(f"   Max: {max(assess_times):.2f} ms")
            print(f"   Avg: {statistics.mean(assess_times):.2f} ms")
            print(f"   Median: {statistics.median(assess_times):.2f} ms")
            print(f"   P95: {sorted(assess_times)[int(len(assess_times)*0.95)]:.2f} ms")
            print(f"   P99: {sorted(assess_times)[int(len(assess_times)*0.99)]:.2f} ms\n")
        
        # Errors
        if self.results["errors"]:
            print(f"❌ ERRORS ({len(self.results['errors'])} total):")
            error_types = {}
            for error in self.results["errors"][:10]:  # Show first 10
                error_type = error.split(":")[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1
                print(f"   • {error}")
            print(f"   ... and {max(0, len(self.results['errors']) - 10)} more\n")
        
        # Recommendations
        print("✅ RECOMMENDATIONS FOR PRODUCTION DEPLOYMENT:")
        if success_rate >= 99:
            print("   ✓ Excellent reliability - system ready for production")
        elif success_rate >= 95:
            print("   ⚠ Good reliability - monitor error rates after deployment")
        else:
            print("   ✗ Failed reliability test - investigate errors before deployment")
        
        if self.results["recommendations"]:
            avg_rec = statistics.mean([r["response_time_ms"] for r in self.results["recommendations"]])
            if avg_rec < 100:
                print("   ✓ Excellent response time - well under 500ms threshold")
            elif avg_rec < 500:
                print("   ⚠ Acceptable response time - consider optimization if server loaded")
            else:
                print("   ✗ Slow response time - investigate database queries or server capacity")
        
        print("="*70 + "\n")
    
    def export_results(self, filename="load_test_results.json"):
        """Export results to JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "students": self.num_students,
                "duration_seconds": self.duration
            },
            "results": self.results,
            "summary": {
                "total_requests": len(self.results["recommendations"]) + len(self.results["assessments"]),
                "errors": len(self.results["errors"]),
                "success_rate_percent": (
                    (len(self.results["recommendations"]) + len(self.results["assessments"]) - len(self.results["errors"])) / 
                    (len(self.results["recommendations"]) + len(self.results["assessments"])) * 100
                    if (len(self.results["recommendations"]) + len(self.results["assessments"])) > 0 else 0
                )
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Results exported to {filename}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Load test for Adaptive Learning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Test with 10 students for 60 seconds
  python load_test.py --students 10 --duration 60
  
  # Test with 100 students for 5 minutes
  python load_test.py --students 100 --duration 300
  
  # Production readiness test (1000 requests over 10 minutes)
  python load_test.py --students 50 --duration 600
        """
    )
    
    parser.add_argument(
        "--students",
        type=int,
        default=10,
        help="Number of test students to register (default: 10)"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="API URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--export",
        help="Export results to JSON file"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("ADAPTIVE LEARNING SYSTEM - LOAD TEST".center(70))
    print("="*70 + "\n")
    
    print(f"⚙️  Configuration:")
    print(f"   API URL: {args.api}")
    print(f"   Test Students: {args.students}")
    print(f"   Duration: {args.duration} seconds\n")
    
    # Check API health
    print("🔍 Checking API health...")
    try:
        response = requests.get(f"{args.api}/health", timeout=2)
        if response.status_code != 200:
            print("❌ API is not responding. Make sure the backend is running:")
            print(f"   cd backend && uvicorn app.main:app --reload")
            return
        print("✅ API is responding\n")
    except:
        print("❌ Cannot connect to API. Make sure the backend is running:")
        print(f"   cd backend && uvicorn app.main:app --reload")
        return
    
    # Run test
    tester = LoadTestRunner(
        api_url=args.api,
        num_students=args.students,
        duration=args.duration
    )
    
    if not tester.setup():
        print("❌ Failed to set up test students")
        return
    
    if tester.run_load_test():
        tester.print_results()
        
        if args.export:
            tester.export_results(args.export)


if __name__ == "__main__":
    main()
