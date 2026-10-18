"""
Enterprise Data Science Core: Pandas Time Series Analysis, Resampling & Parquet Columnar Storage
================================================================================================

This module delivers a comprehensive, production-grade guide to high-frequency time series
manipulation, temporal frequency downsampling, rolling window aggregations, exponential moving
averages (EMA), and Apache Parquet columnar I/O, contrasted against Node.js and PHP architectures.

Architectural Polyglot Comparison:
----------------------------------
1. Time Series Representation:
   - Node.js (TypeScript):
     Dates are represented by JS `Date` objects (milliseconds since Unix epoch) or ISO 8601 strings.
     Libraries like `date-fns` or `dayjs` operate on individual objects. Large arrays of Date objects
     suffer from massive heap overhead (pointer chasing, V8 object wrappers).
   - PHP (Laravel):
     Laravel leverages `Carbon\\Carbon` / `CarbonImmutable` (wrapping PHP `DateTime`). Each timestamp
     instantiates a full PHP object (`zval` + `zend_object`), causing severe memory amplification
     when processing hundreds of thousands of temporal telemetry records.
   - Python (Pandas):
     Timestamps are represented as contiguous 64-bit signed integers (`datetime64[ns]`), recording
     nanoseconds since the Unix epoch in unboxed C memory buffers. Slicing by time ranges (e.g.
     `df['2026-03-01':'2026-03-07']`) is an O(log N) binary search operation over sorted indices.

2. Resampling & Window Metrics:
   - Node.js:
     Downsampling requires manual timestamp quantization:
     `Math.floor(ts / (86400 * 1000)) * (86400 * 1000)` into a Map, followed by manual looping.
     Rolling windows require custom circular ring buffers or sliding double-ended queues.
   - PHP:
     Requires iterating over collections, formatting strings via `$carbon->format('Y-m-d')`,
     and grouping. Rolling computations require nested array slicing and iterative mathematical functions.
   - Pandas:
     `df.resample('1D').agg(...)` invokes Cython timestamp grouping algorithms.
     `df.rolling(window=7).mean()` executes vectorized SIMD sliding-window algorithms in C.
     `df.ewm(span=7).mean()` computes Exponential Moving Averages analytically in compiled code.

3. Serialization: Columnar Parquet vs CSV / JSON:
   - Node.js & PHP:
     Predominantly serialize datasets to JSON or CSV. Both are row-oriented text formats requiring
     expensive string parsing, high disk footprint, and zero column pruning or predicate pushdown.
   - Pandas (via PyArrow):
     `to_parquet()` writes binary columnar files with Snappy/ZSTD dictionary compression and metadata
     statistics. Readers can project specific columns (`columns=['latency_ms']`) without reading
     unneeded columns from disk, reducing I/O bandwidth by 80-95%.

Official Documentation References:
- Pandas Time Series / Date Functionality:
  https://pandas.pydata.org/docs/user_guide/timeseries.html
- Pandas DataFrame.resample:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
- Pandas DataFrame.rolling:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html
- Pandas DataFrame.ewm (Exponential Weighted Functions):
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html
- Pandas DataFrame.to_parquet:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html
- Pandas read_parquet:
  https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configure UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


# ==============================================================================
# 1. Dataset Generation: High-Frequency Microservice Telemetry
# ==============================================================================


def generate_hourly_telemetry_series(days: int = 14) -> pd.DataFrame:
    """
    Generate synthetic hourly cloud API telemetry data spanning multiple days.
    Constructs an explicit DatetimeIndex for chronological indexing.
    """
    total_hours = days * 24
    # Create contiguous hourly timestamp range (e.g. 2026-03-01 to 2026-03-14)
    timestamps = pd.date_range(start="2026-03-01 00:00:00", periods=total_hours, freq="h")

    # Generate synthetic metrics with deterministic pseudo-random seed
    np.random.seed(42)
    base_rps = 500.0 + 200.0 * np.sin(np.linspace(0, days * 2 * np.pi, total_hours))
    noise = np.random.normal(0, 30.0, total_hours)
    request_counts = np.maximum(50.0, base_rps + noise).astype(int)

    # Latencies in milliseconds (correlated with request traffic)
    latency_ms = 45.0 + (request_counts / 25.0) + np.random.exponential(5.0, total_hours)

    # Error counts (occasional spikes)
    error_counts = np.random.poisson(lam=1.5, size=total_hours)

    df = pd.DataFrame(
        {
            "request_count": request_counts,
            "latency_ms": latency_ms.round(2),
            "error_count": error_counts,
        },
        index=timestamps,
    )
    df.index.name = "timestamp"
    return df


# ==============================================================================
# 2. Resampling & Frequency Conversion (Downsampling)
# ==============================================================================


def downsample_telemetry(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Downsample high-frequency hourly telemetry into daily and 6-hour aggregate buckets.

    Polyglot Comparison:
    - Node.js (TypeScript):
      ```typescript
      // Manual grouping by date string
      const daily = new Map<string, { requests: number; latencySum: number; count: number }>();
      for (const row of telemetry) {
          const dayKey = row.timestamp.toISOString().split('T')[0];
          if (!daily.has(dayKey)) daily.set(dayKey, { requests: 0, latencySum: 0, count: 0 });
          const acc = daily.get(dayKey)!;
          acc.requests += row.requestCount;
          acc.latencySum += row.latencyMs;
          acc.count++;
      }
      ```
    - PHP (Laravel):
      ```php
      $daily = $telemetry->groupBy(function ($row) {
          return $row->timestamp->format('Y-m-d');
      })->map(function ($group) {
          return [
              'total_requests' => $group->sum('request_count'),
              'avg_latency'    => $group->avg('latency_ms'),
              'max_latency'    => $group->max('latency_ms'),
          ];
      });
      ```
    - Pandas:
      `df.resample('1D').agg(...)` invokes Cython timestamp grouping algorithms without
      materializing string objects or hash tables.
    """
    # Define aggregation rules per metric
    agg_rules = {
        "request_count": "sum",
        "latency_ms": ["mean", "max"],
        "error_count": "sum",
    }

    # 1. Downsample to Daily frequency ('1D')
    daily_resampled = df.resample("1D").agg(agg_rules)
    daily_resampled.columns = ["total_requests", "avg_latency_ms", "max_latency_ms", "total_errors"]
    daily_resampled["avg_latency_ms"] = daily_resampled["avg_latency_ms"].round(2)

    # 2. Downsample to 6-Hour frequency ('6h')
    six_hour_resampled = df.resample("6h").agg({"request_count": "sum", "latency_ms": "mean"})
    six_hour_resampled.columns = ["requests_6h", "avg_latency_6h"]

    return daily_resampled, six_hour_resampled


# ==============================================================================
# 3. Rolling Windows & Exponential Moving Averages (EMA)
# ==============================================================================


def compute_rolling_and_exponential_metrics(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 7-day Simple Moving Average (SMA), Rolling Standard Deviation, and
    Exponential Moving Average (EMA).

    Polyglot Comparison:
    - Node.js:
      Requires maintaining a sliding window array (length W), pushing new items,
      popping old items, and recomputing the sum and variance manually.
    - PHP:
      Requires `array_slice` across sliding indices in a `for` loop, incurring O(W * N) time complexity.
    - Pandas:
      `df['col'].rolling(window=7, min_periods=1).mean()` runs in O(N) time using SIMD
      vectorized algorithms in compiled C.
      `df['col'].ewm(span=7, adjust=False).mean()` computes recursive exponential smoothing:
      y_t = (1 - alpha) * y_{t-1} + alpha * x_t.
    """
    result = daily_df.copy()

    # 7-day Simple Moving Average on daily total requests
    result["requests_sma_7d"] = (
        result["total_requests"].rolling(window=7, min_periods=1).mean().round(2)
    )

    # 7-day Rolling Standard Deviation (Volatility Metric)
    result["requests_std_7d"] = (
        result["total_requests"].rolling(window=7, min_periods=1).std().fillna(0.0).round(2)
    )

    # 7-day Exponential Moving Average (EMA) gives higher weight to recent days
    result["requests_ema_7d"] = (
        result["total_requests"].ewm(span=7, adjust=False).mean().round(2)
    )

    return result


# ==============================================================================
# 4. Columnar Apache Parquet I/O vs Row-Oriented Storage
# ==============================================================================


def benchmark_parquet_vs_csv(df: pd.DataFrame, output_dir: Path) -> Tuple[int, int, pd.DataFrame]:
    """
    Benchmark disk storage and round-trip fidelity between Apache Parquet and standard CSV.

    Polyglot Comparison:
    - Node.js & PHP:
      Default to JSON (`JSON.stringify()`, `json_encode()`) or CSV. Uncompressed text formats
      are bloated and require parsing every single character on load.
    - Pandas + PyArrow:
      Parquet uses Snappy dictionary compression, run-length encoding (RLE), and columnar chunking.
      Readers can project only desired columns (`columns=['latency_ms']`) without reading or
      decoding other columns from disk.
    """
    csv_path = output_dir / "telemetry_benchmark.csv"
    parquet_path = output_dir / "telemetry_benchmark.parquet"

    # Export to CSV
    df.to_csv(csv_path, index=True)
    csv_bytes = csv_path.stat().st_size

    # Export to Columnar Parquet with Snappy compression (via pyarrow engine)
    df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=True)
    parquet_bytes = parquet_path.stat().st_size

    # Round-trip read: verify lossless reconstruction
    df_restored = pd.read_parquet(parquet_path, engine="pyarrow")

    # Column-pruned read: demonstrate zero-overhead projection
    df_pruned = pd.read_parquet(parquet_path, columns=["total_requests", "requests_sma_7d"])
    assert list(df_pruned.columns) == ["total_requests", "requests_sma_7d"]

    return csv_bytes, parquet_bytes, df_restored


# ==============================================================================
# 5. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying DatetimeIndex, resampling, rolling stats, and Parquet I/O."""
    console.print(
        Panel.fit(
            "[bold cyan]Data Science Core: Time Series, Resampling & Parquet[/bold cyan]\n"
            "[dim]Verifying DatetimeIndex slicing, frequency resampling, rolling/EMA windows, and PyArrow Parquet I/O.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Dataset Generation
    console.print("[dim]Phase 1: Generating 14-day hourly microservice telemetry...[/dim]")
    hourly_df = generate_hourly_telemetry_series(days=14)
    assert len(hourly_df) == 14 * 24 == 336
    assert isinstance(hourly_df.index, pd.DatetimeIndex)
    assert hourly_df.index.freqstr == "h" or hourly_df.index.inferred_freq == "h"
    console.print(f"  [green][PASS] Generated {len(hourly_df)} hourly records with DatetimeIndex.[/green]")

    # 2. Datetime Slicing Verification
    console.print("[dim]Phase 2: Validating chronological timestamp slicing...[/dim]")
    # Slicing by date string range: '2026-03-01' to '2026-03-03' inclusive (3 days * 24h = 72 rows)
    three_day_slice = hourly_df.loc["2026-03-01":"2026-03-03"]
    assert len(three_day_slice) == 72
    console.print("  [green][PASS] Datetime range slicing verified (3 days = 72 records).[/green]")

    # 3. Frequency Resampling Verification
    console.print("[dim]Phase 3: Resampling hourly series to Daily (1D) and 6-Hour (6h)...[/dim]")
    daily_df, six_hour_df = downsample_telemetry(hourly_df)
    assert len(daily_df) == 14
    assert len(six_hour_df) == 14 * 4 == 56

    # Verify daily total requests equal sum of respective hourly requests
    first_day_hourly_sum = hourly_df.loc["2026-03-01", "request_count"].sum()
    assert daily_df.loc["2026-03-01", "total_requests"] == first_day_hourly_sum
    console.print(f"  [green][PASS] Resampling verified: 336 hourly rows -> 14 daily rows (First day requests: {first_day_hourly_sum:,}).[/green]")

    # 4. Rolling Window & EMA Verification
    console.print("[dim]Phase 4: Computing rolling 7-day Simple Moving Average & EMA...[/dim]")
    metrics_df = compute_rolling_and_exponential_metrics(daily_df)
    assert "requests_sma_7d" in metrics_df.columns
    assert "requests_ema_7d" in metrics_df.columns

    # Day 1: SMA equals Day 1 value because min_periods=1
    assert metrics_df.iloc[0]["requests_sma_7d"] == metrics_df.iloc[0]["total_requests"]

    # Day 7: SMA equals arithmetic mean of days 1 through 7
    day_7_expected_sma = round(metrics_df.iloc[0:7]["total_requests"].mean(), 2)
    assert np.isclose(metrics_df.iloc[6]["requests_sma_7d"], day_7_expected_sma, atol=0.02)
    console.print(f"  [green][PASS] Rolling window verified: Day 7 SMA = {metrics_df.iloc[6]['requests_sma_7d']:,} requests.[/green]")

    # 5. Apache Parquet Columnar Serialization Verification
    console.print("[dim]Phase 5: Benchmarking Apache Parquet (PyArrow) vs CSV disk storage...[/dim]")
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        csv_bytes, parquet_bytes, restored_df = benchmark_parquet_vs_csv(metrics_df, temp_path)

        # Verify lossless round-trip
        pd.testing.assert_frame_equal(metrics_df, restored_df, check_freq=False)

        # Validate compression efficiency
        compression_ratio = csv_bytes / parquet_bytes if parquet_bytes > 0 else 1.0
        console.print(
            f"  [green][PASS] Parquet I/O verified: CSV={csv_bytes} bytes, Parquet={parquet_bytes} bytes "
            f"(Compression ratio: {compression_ratio:.2f}x). Round-trip lossless.[/green]"
        )

    # Architectural Summary Table
    table = Table(title="Pandas Time Series vs Node.js & PHP Architecture", border_style="green")
    table.add_column("Capability", style="bold cyan")
    table.add_column("Pandas (PyArrow)", style="white")
    table.add_column("Node.js (TypeScript)", style="yellow")
    table.add_column("PHP (Laravel)", style="magenta")

    table.add_row(
        "Timestamp Representation",
        "Contiguous `int64` (`datetime64[ns]`)",
        "V8 `Date` objects or ISO strings",
        "`Carbon` / `DateTime` PHP objects",
    )
    table.add_row(
        "Downsampling (Resample)",
        "`df.resample('1D').mean()` in Cython",
        "`Math.floor()` into Map with manual sum",
        "`$carbon->format('Y-m-d')` into Group",
    )
    table.add_row(
        "Rolling Windows",
        "`df.rolling(7).mean()` vectorized C",
        "Custom ring buffer / sliding deque",
        "Iterative array slicing in for loop",
    )
    table.add_row(
        "Exponential Smoothing",
        "`df.ewm(span=7).mean()` analytic",
        "Custom recursive math loop",
        "Custom loop calculation",
    )
    table.add_row(
        "Storage & Projection",
        "Columnar Parquet with Snappy & pruning",
        "Text JSON / CSV (full parse required)",
        "Text JSON / CSV or MySQL table",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
