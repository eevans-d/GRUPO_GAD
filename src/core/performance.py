# -*- coding: utf-8 -*-
"""
Performance monitoring and optimization utilities for GRUPO_GAD.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger

performance_logger = get_logger("performance")


class QueryPerformanceTracker:
    """
    Tracks database query performance for optimization insights.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.slow_query_threshold = 1.0  # 1 second threshold for slow queries
        self.query_stats: Dict[str, Dict[str, Any]] = {}
    
    def record_query(self, query: str, duration: float, error: Optional[str] = None) -> None:
        """Record query execution statistics."""
        if not self.enabled:
            return
            
        # Extract query type (SELECT, INSERT, UPDATE, DELETE)
        query_type = query.strip().upper().split()[0] if query.strip() else "UNKNOWN"
        
        # Update statistics
        if query_type not in self.query_stats:
            self.query_stats[query_type] = {
                "count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "max_duration": 0.0,
                "slow_queries": 0,
                "errors": 0
            }
        
        stats = self.query_stats[query_type]
        stats["count"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["count"]
        stats["max_duration"] = max(stats["max_duration"], duration)
        
        if duration > self.slow_query_threshold:
            stats["slow_queries"] += 1
            performance_logger.warning(
                "Slow query detected",
                query_type=query_type,
                duration=duration,
                query=query[:200] + "..." if len(query) > 200 else query
            )
        
        if error:
            stats["errors"] += 1
            performance_logger.error(
                "Query error",
                query_type=query_type,
                error=Exception(error) if isinstance(error, str) else error,
                query=query[:200] + "..." if len(query) > 200 else query,
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            "enabled": self.enabled,
            "slow_query_threshold": self.slow_query_threshold,
            "statistics": dict(self.query_stats),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_statistics(self) -> None:
        """Reset all performance statistics."""
        self.query_stats.clear()


# Global query performance tracker
query_tracker = QueryPerformanceTracker()


@asynccontextmanager
async def track_query_performance(session: AsyncSession, operation_name: str = "unknown") -> AsyncGenerator[None, None]:
    """
    Context manager to track query performance for a database operation.
    """
    start_time = time.time()
    error_occurred = None
    
    try:
        yield
    except Exception as e:
        error_occurred = e
        raise
    finally:
        duration = time.time() - start_time
        query_tracker.record_query(
            query=f"OPERATION:{operation_name}",
            duration=duration,
            error=str(error_occurred) if error_occurred is not None else None,
        )


async def analyze_slow_queries(session: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Analyze slow queries from PostgreSQL's pg_stat_statements extension.
    """
    try:
        # This requires pg_stat_statements extension to be enabled
        query = text("""
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                stddev_exec_time,
                rows
            FROM pg_stat_statements 
            WHERE mean_exec_time > :threshold
            ORDER BY mean_exec_time DESC 
            LIMIT :limit
        """)
        
        result = await session.execute(query, {
            "threshold": query_tracker.slow_query_threshold * 1000,  # Convert to ms
            "limit": limit
        })
        
        slow_queries = []
        for row in result:
            slow_queries.append({
                "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                "calls": row.calls,
                "total_exec_time_ms": round(row.total_exec_time, 2),
                "mean_exec_time_ms": round(row.mean_exec_time, 2),
                "stddev_exec_time_ms": round(row.stddev_exec_time, 2) if row.stddev_exec_time else 0,
                "rows": row.rows
            })
        
        return slow_queries
    
    except Exception as e:
        performance_logger.warning(
            f"Could not analyze slow queries: {e}. pg_stat_statements extension may not be enabled."
        )
        return []


async def suggest_database_indexes(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Suggest missing indexes based on query patterns.
    """
    try:
        # Query to find missing indexes from pg_stat_user_tables
        query = text("""
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                CASE 
                    WHEN seq_scan > 0 THEN seq_tup_read / seq_scan::float 
                    ELSE 0 
                END as avg_seq_tup_read
            FROM pg_stat_user_tables 
            WHERE seq_scan > 100  -- Tables with many sequential scans
            AND schemaname = 'gad'  -- Focus on our schema
            ORDER BY seq_tup_read DESC
            LIMIT 10
        """)
        
        result = await session.execute(query)
        
        suggestions = []
        for row in result:
            if row.avg_seq_tup_read > 1000:  # Threshold for suggesting indexes
                suggestions.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "sequential_scans": row.seq_scan,
                    "sequential_tuples_read": row.seq_tup_read,
                    "avg_tuples_per_scan": round(row.avg_seq_tup_read, 2),
                    "recommendation": f"Consider adding indexes to frequently queried columns in {row.tablename}",
                    "index_coverage": round(
                        (row.idx_tup_fetch or 0)
                        / max(row.seq_tup_read + (row.idx_tup_fetch or 0), 1)
                        * 100,
                        2,
                    )
                })
        
        return suggestions
    
    except Exception as e:
        performance_logger.warning(f"Could not analyze index suggestions: {e}")
        return []


class PerformanceMiddleware:
    """
    Middleware to track API endpoint performance.
    """
    
    def __init__(self) -> None:
        self.endpoint_stats: Dict[str, Dict[str, Any]] = {}
    
    def record_request(self, method: str, path: str, duration: float, status_code: int) -> None:
        """Record API request performance."""
        endpoint_key = f"{method} {path}"
        
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                "count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "max_duration": 0.0,
                "status_codes": {},
                "errors": 0
            }
        
        stats = self.endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["count"]
        stats["max_duration"] = max(stats["max_duration"], duration)
        
        # Track status codes
        status_key = str(status_code)
        stats["status_codes"][status_key] = stats["status_codes"].get(status_key, 0) + 1
        
        if status_code >= 400:
            stats["errors"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current endpoint performance statistics."""
        return {
            "endpoints": dict(self.endpoint_stats),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest endpoints by average response time."""
        sorted_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["avg_duration"],
            reverse=True
        )
        
        return [
            {
                "endpoint": endpoint,
                "avg_duration_ms": round(stats["avg_duration"] * 1000, 2),
                "max_duration_ms": round(stats["max_duration"] * 1000, 2),
                "request_count": stats["count"],
                "error_rate": round(stats["errors"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
            }
            for endpoint, stats in sorted_endpoints[:limit]
        ]


# Global performance middleware instance
performance_middleware = PerformanceMiddleware()