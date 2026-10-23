import time
import requests
import statistics
import concurrent.futures

API_URL = "http://localhost:8000/v1/chat/completions"
API_KEY = "1234"

def send_request(prompt, max_tokens=50):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": "/model-cache",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": True
    }
    
    start_time = time.time()
    ttft = None
    total_tokens = 0
    
    try:
        with requests.post(API_URL, headers=headers, json=data, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    if b'"content"' in line:  # Приблизительный подсчет токенов
                        total_tokens += 1
                    if ttft is None and b'"content"' in line:
                        ttft = time.time() - start_time
    except Exception as e:
        return {"error": str(e)}
    
    end_time = time.time()
    latency = end_time - start_time
    throughput = total_tokens / latency if latency > 0 else 0
    
    return {
        "ttft": ttft if ttft else 0,
        "latency": latency,
        "throughput": throughput,
        "tokens": total_tokens
    }

def run_test(prompt, num_requests=5):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(send_request, prompt) for _ in range(num_requests)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    return results

if __name__ == "__main__":
    short_prompt = "Привет! Как дела?"
    long_prompt = "Напиши подробное эссе о том, как работает Kubernetes, включая описание архитектуры, основных компонентов (etcd, kube-apiserver, kube-scheduler, kube-controller-manager, kubelet, kube-proxy), а также объясни, как происходит планирование подов и как работает сеть в кластере. Приведи примеры использования в реальных проектах."
    
    print("=== Тест 1: Короткие промпты ===")
    short_results = run_test(short_prompt, num_requests=5)
    for r in short_results:
        print(f"TTFT: {r['ttft']:.4f}s, Latency: {r['latency']:.4f}s, Throughput: {r['throughput']:.2f} tok/s")
    
    print("\n=== Тест 2: Длинные промпты ===")
    long_results = run_test(long_prompt, num_requests=3)
    for r in long_results:
        print(f"TTFT: {r['ttft']:.4f}s, Latency: {r['latency']:.4f}s, Throughput: {r['throughput']:.2f} tok/s")
    
    print("\n=== Аналитика ===")
    print("А) Для потока коротких запросов: увеличьте --max-num-seqs и VLLM_CPU_KVCACHE_SPACE.")
    print("Б) Для длинных контекстов: увеличьте --max-model-len и включите --enable-chunked-prefill.")
