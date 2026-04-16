"""
Canary deployment script for LLM service.

Usage:
    python scripts/canary_deploy.py --image aimsa-llm:v2 --weight 10

Flow:
    1. Deploy new version as canary (0% traffic)
    2. Gradually increase traffic weight
    3. Monitor error rate at each step
    4. If error rate > threshold → rollback
    5. If stable at 100% → promote to stable
"""
import argparse
import subprocess
import sys
import time


def run_kubectl(args: list[str]) -> str:
    result = subprocess.run(["kubectl"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ kubectl error: {result.stderr}")
        sys.exit(1)
    return result.stdout


def deploy_canary(image: str):
    print(f"[1/4] Deploying canary with image: {image}")
    run_kubectl([
        "set", "image", "deployment/llm-service",
        f"llm-service={image}",
        "--namespace=aimsa",
    ])
    run_kubectl([
        "patch", "deployment", "llm-service",
        "--type=json",
        '-p=[{"op":"add","path":"/spec/template/metadata/labels/track","value":"canary"}]',
        "--namespace=aimsa",
    ])
    print("  ✅ Canary deployment created")


def set_canary_weight(weight: int):
    print(f"[2/4] Setting canary weight to {weight}%")
    run_kubectl([
        "annotate", "ingress", "llm-canary-ingress",
        f"nginx.ingress.kubernetes.io/canary-weight={weight}",
        "--overwrite",
        "--namespace=aimsa",
    ])
    print(f"  ✅ Canary weight set to {weight}%")


def check_error_rate() -> float:
    print("[3/4] Checking error rate...")
    try:
        output = run_kubectl([
            "exec", "deployment/backend", "--namespace=aimsa", "--",
            "python", "-c",
            "import httpx; r=httpx.get('http://llm-service:8001/health'); print(r.status_code)"
        ])
        if "200" in output:
            print("  ✅ Health check passed")
            return 0.0
    except Exception:
        pass
    print("  ⚠️ Health check failed")
    return 1.0


def promote_canary():
    print("[4/4] Promoting canary to stable...")
    run_kubectl([
        "patch", "deployment", "llm-service",
        "--type=json",
        '-p=[{"op":"replace","path":"/spec/template/metadata/labels/track","value":"stable"}]',
        "--namespace=aimsa",
    ])
    set_canary_weight(0)
    print("  ✅ Canary promoted to stable")


def rollback():
    print("🔄 Rolling back canary...")
    run_kubectl(["rollout", "undo", "deployment/llm-service", "--namespace=aimsa"])
    set_canary_weight(0)
    print("  ✅ Rolled back to previous stable")


def main():
    parser = argparse.ArgumentParser(description="Canary deployment for LLM service")
    parser.add_argument("--image", required=True, help="New image to deploy")
    parser.add_argument("--weight", type=int, default=10, help="Canary traffic weight (%%)")
    parser.add_argument("--error-threshold", type=float, default=0.1, help="Max error rate before rollback")
    args = parser.parse_args()

    deploy_canary(args.image)
    time.sleep(10)

    weights = [5, 10, 25, 50, 100] if args.weight == 100 else [args.weight]
    for w in weights:
        set_canary_weight(w)
        time.sleep(30)
        error_rate = check_error_rate()
        if error_rate > args.error_threshold:
            print(f"❌ Error rate {error_rate:.0%} exceeds threshold {args.error_threshold:.0%}")
            rollback()
            sys.exit(1)

    if args.weight == 100:
        promote_canary()
    else:
        print(f"✅ Canary running at {args.weight}%. Monitor and promote when ready.")


if __name__ == "__main__":
    main()
