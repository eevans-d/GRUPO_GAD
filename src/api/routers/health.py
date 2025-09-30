# -*- coding: utf-8 -*-
"""
Enhanced Health Check endpoint with comprehensive monitoring.
"""

import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from src.core.database import get_db_session, db_circuit_breaker
from src.core.performance import query_tracker, performance_middleware, analyze_slow_queries, suggest_database_indexes


router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for load balancers.
    """
    # Mantener respuesta mínima para compatibilidad con tests y balancers
    return {"status": "ok"}


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check with database and system status.
    """
    start_time = time.time()
    health_status: Dict[str, Any] = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Database connectivity check
    db_status = "ok"
    db_response_time = None
    db_error = None

    try:
        db_start = time.time()
        async for session in get_db_session():
            # Simple connectivity test
            await session.execute(text("SELECT 1"))
            db_response_time = round((time.time() - db_start) * 1000, 2)
            break
    except Exception as e:
        db_status = "error"
        db_error = str(e)
        health_status["status"] = "degraded"

    db_check: Dict[str, Any] = {
        "status": db_status,
        "response_time_ms": db_response_time,
        "circuit_breaker_open": db_circuit_breaker.open,
        "circuit_breaker_failures": db_circuit_breaker.failures,
        "error": db_error
    }
    health_status["checks"]["database"] = db_check

    # System checks
    # Cálculo de uptime en dos pasos para mantener líneas cortas
    _start = getattr(health_check, "_start_time", 0)
    uptime = int(time.time() - _start) if _start else 0
    system_check: Dict[str, Any] = {
        "status": "ok",
        "uptime_seconds": uptime,
    }
    health_status["checks"]["system"] = system_check

    # Overall response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    # Return appropriate HTTP status
    if health_status["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return health_status


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    """
    try:
        # Test database connectivity
        async for session in get_db_session():
            await session.execute(text("SELECT 1"))
            break
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/performance")
async def performance_metrics() -> Dict[str, Any]:
    """
    Performance metrics endpoint for monitoring and optimization.
    """
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "query_performance": query_tracker.get_statistics(),
        "endpoint_performance": performance_middleware.get_statistics(),
        "slowest_endpoints": performance_middleware.get_slowest_endpoints(5),
    }

    # Add database-specific performance insights if available
    try:
        async for session in get_db_session():
            metrics["slow_queries"] = await analyze_slow_queries(session, limit=5)
            metrics["index_suggestions"] = await suggest_database_indexes(session)
            break
    except Exception as e:
        metrics["database_analysis_error"] = str(e)

    return metrics


# Initialize start time for uptime calculation (dynamic attribute for uptime)
health_check._start_time = time.time()  # type: ignore[attr-defined]
