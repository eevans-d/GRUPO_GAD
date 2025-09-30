# -*- coding: utf-8 -*-
"""
PostGIS geospatial service for GRUPO_GAD.

Provides functionality for spatial queries using PostGIS geography types
with SRID 4326 for accurate distance calculations.
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException

from src.core.logging import get_logger

logger = get_logger("core.geo.postgis")


async def find_nearest_efectivo(
    db: AsyncSession, 
    lat: float, 
    lng: float, 
    limit: int = 1
) -> List[Dict[str, Any]]:
    """
    Find the nearest efectivos to a given location using PostGIS.
    
    Uses geography types for accurate distance calculations in meters.
    Only works with PostgreSQL + PostGIS.
    
    Args:
        db: Database session
        lat: Latitude (-90 to 90)
        lng: Longitude (-180 to 180)
        limit: Maximum number of results to return
        
    Returns:
        List of dicts with keys: efectivo_id, distance_m
        
    Raises:
        HTTPException: 503 if not using PostgreSQL dialect
    """
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
    if not (-180 <= lng <= 180):
        raise ValueError(f"Invalid longitude: {lng}. Must be between -180 and 180.")
    
    # Check if we're using PostgreSQL
    if db.bind.dialect.name != 'postgresql':
        logger.error(
            "PostGIS operations require PostgreSQL dialect",
            dialect=db.bind.dialect.name
        )
        raise HTTPException(
            status_code=503,
            detail="Geospatial operations not available - PostgreSQL/PostGIS required"
        )
    
    try:
        # Query using geography for accurate distance calculation in meters
        query = text("""
            SELECT 
                id as efectivo_id,
                ST_Distance(
                    geom, 
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) AS distance_m
            FROM efectivos 
            WHERE geom IS NOT NULL 
                AND deleted_at IS NULL
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            LIMIT :limit
        """)
        
        result = await db.execute(
            query, 
            {"lat": lat, "lng": lng, "limit": limit}
        )
        
        rows = result.fetchall()
        
        # Convert to list of dicts
        efectivos = []
        for row in rows:
            efectivos.append({
                "efectivo_id": row.efectivo_id,
                "distance_m": float(row.distance_m) if row.distance_m is not None else 0.0
            })
        
        logger.info(
            f"Found {len(efectivos)} nearest efectivos",
            lat=lat,
            lng=lng,
            limit=limit,
            results_count=len(efectivos)
        )
        
        return efectivos
        
    except Exception as e:
        logger.error(
            "Error executing PostGIS query",
            error=e,
            lat=lat,
            lng=lng,
            limit=limit
        )
        # Re-raise as HTTP exception for API endpoints
        raise HTTPException(
            status_code=503,
            detail=f"Geospatial query failed: {str(e)}"
        )