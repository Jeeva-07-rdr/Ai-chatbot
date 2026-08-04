import time
import os
import logging

logger = logging.getLogger('umi')


class PerformanceTracer:
    """
    High-Precision Enterprise Performance Instrumentation Tracer for UMI AI Chatbot.
    Tracks timing across all request lifecycle stages, database execution, AI latency,
    token counts, throughput, and system resource utilization.
    """
    def __init__(self, request_name="Chat Request"):
        self.request_name = request_name
        self.start_time = time.perf_counter()
        self.timestamps = {'Request Received': 0.0}
        self.stage_durations = {}
        self.metrics = {
            'db_time': 0.0,
            'api_time': 0.0,
            'prompt_tokens': 0,
            'output_tokens': 0,
            'context_tokens': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'ttft': 0.0
        }
        self.last_mark = self.start_time

    def mark(self, stage_name):
        now = time.perf_counter()
        elapsed = now - self.start_time
        stage_delta = now - self.last_mark
        self.timestamps[stage_name] = round(elapsed, 4)
        self.stage_durations[stage_name] = round(stage_delta, 4)
        self.last_mark = now

    def add_db_time(self, duration):
        self.metrics['db_time'] += round(duration, 4)

    def add_api_time(self, duration):
        self.metrics['api_time'] += round(duration, 4)

    def set_tokens(self, prompt_tokens, output_tokens):
        self.metrics['prompt_tokens'] = prompt_tokens
        self.metrics['output_tokens'] = output_tokens
        self.metrics['context_tokens'] = prompt_tokens + output_tokens

    def record_cache_hit(self):
        self.metrics['cache_hits'] += 1

    def record_cache_miss(self):
        self.metrics['cache_misses'] += 1

    def generate_report(self):
        total_time = round(time.perf_counter() - self.start_time, 4)
        output_tokens = self.metrics['output_tokens']
        gen_time = self.stage_durations.get('Generation Time', total_time)
        tps = round(output_tokens / gen_time, 2) if gen_time > 0 and output_tokens > 0 else 0.0
        
        total_cache_ops = self.metrics['cache_hits'] + self.metrics['cache_misses']
        hit_rate = round((self.metrics['cache_hits'] / total_cache_ops) * 100, 1) if total_cache_ops > 0 else 100.0

        report = [
            "\n========================================",
            f"UMI PERFORMANCE REPORT: {self.request_name.upper()}",
            "========================================"
        ]
        
        for stage, duration in self.timestamps.items():
            report.append(f"{stage:<25}: {duration:.4f}s")
            
        report.extend([
            "----------------------------------------",
            f"Total Response Time      : {total_time:.4f}s",
            f"Context Tokens           : ~{self.metrics['context_tokens']}",
            f"Prompt Tokens            : ~{self.metrics['prompt_tokens']}",
            f"Output Tokens            : ~{self.metrics['output_tokens']}",
            f"Tokens/sec               : {tps:.2f} t/s",
            f"Database Time            : {self.metrics['db_time']:.4f}s",
            f"API Time                 : {self.metrics['api_time']:.4f}s",
            f"Cache Hit Rate           : {hit_rate}%",
            "========================================\n"
        ])
        
        full_report_str = "\n".join(report)
        logger.info(full_report_str)
        return full_report_str
