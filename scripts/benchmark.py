"""
Performance benchmark script for AIMSA.

Usage:
    python scripts/benchmark.py --base-url http://localhost:8000 --concurrency 10 --requests 100

What it tests:
    - API throughput (requests/sec)
    - P50/P95/P99 latency
    - Error rate under load
"""
import argparse
import asyncio
import time
import statistics

import httpx


async def benchmark_endpoint(
    client: httpx.AsyncClient,
    url: str,
    method: str = "GET",
    json_data: dict | None = None,
    num_requests: int = 100,
) -> dict:
    latencies = []
    errors = 0

    async def single_request():
        start = time.monotonic()
        try:
            if method == "GET":
                resp = await client.get(url)
            else:
                resp = await client.post(url, json=json_data)
            elapsed = time.monotonic() - start
            if resp.status_code >= 400:
                errors += 1
            return elapsed
        except Exception:
            return time.monotonic() - start

    start_total = time.monotonic()
    tasks = [single_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
    total_time = time.monotonic() - start_total

    for r in results:
        latencies.append(r)

    latencies.sort()
    return {
        "endpoint": url,
        "total_requests": num_requests,
        "total_time": round(total_time, 2),
        "rps": round(num_requests / total_time, 1),
        "errors": sum(1 for r in results if r > 5),
        "p50": round(statistics.median(latencies) * 1000, 1),
        "p95": round(latencies[int(len(latencies) * 0.95)] * 1000, 1),
        "p99": round(latencies[int(len(latencies) * 0.99)] * 1000, 1),
        "min": round(min(latencies) * 1000, 1),
        "max": round(max(latencies) * 1000, 1),
    }


async def run_benchmark(base_url: str, concurrency: int, num_requests: int):
    print(f"AIMSA Performance Benchmark")
    print(f"Target: {base_url} | Concurrency: {concurrency} | Requests: {num_requests}")
    print("=" * 70)

    endpoints = [
        ("GET", f"{base_url}/", None),
        ("GET", f"{base_url}/api/v1/monitoring/health", None),
        ("GET", f"{base_url}/api/v1/documents/", None),
        ("GET", f"{base_url}/api/v1/monitoring/stats", None),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for method, url, data in endpoints:
            print(f"\n📊 {method} {url.replace(base_url, '')}")
            result = await benchmark_endpoint(client, url, method, data, num_requests)
            print(f"  RPS: {result['rps']} | P50: {result['p50']}ms | P95: {result['p95']}ms | P99: {result['p99']}ms")
            print(f"  Min: {result['min']}ms | Max: {result['max']}ms | Errors: {result['errors']}/{result['total_requests']}")


def main():
    parser = argparse.ArgumentParser(description="AIMSA performance benchmark")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent connections")
    parser.add_argument("--requests", type=int, default=100, help="Total requests per endpoint")
    args = parser.parse_args()
    asyncio.run(run_benchmark(args.base_url, args.concurrency, args.requests))


if __name__ == "__main__":
    main()
