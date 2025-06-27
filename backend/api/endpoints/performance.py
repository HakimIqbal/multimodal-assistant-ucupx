from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import time
import asyncio
import os
from iron_cache import IronCache
from api.auth.auth_middleware import get_current_user
import httpx

router = APIRouter()

class PerformanceMetric(BaseModel):
    id: Optional[str] = None
    endpoint: str
    method: str
    response_time: float
    status_code: int
    user_id: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CacheConfig(BaseModel):
    key: str
    value: Any
    ttl: int = 3600  # Time to live in seconds
    tags: Optional[List[str]] = None

class LoadBalancerConfig(BaseModel):
    service_name: str
    instances: List[str]
    health_check_url: str
    load_balancing_algorithm: str = "round_robin"  # round_robin, least_connections, weighted

# In-memory cache fallback (for local dev if IronCache not available)
memory_cache = {}

class CacheManager:
    """Cache management system using IronCache"""
    def __init__(self):
        self.token = os.getenv("IRON_IO_TOKEN", "")
        self.project_id = os.getenv("IRON_IO_PROJECT_ID", "")
        self.cache_name = os.getenv("IRON_IO_CACHE_NAME", "default-cache")
        self.iron_available = bool(self.token and self.project_id)
        if self.iron_available:
            self.client = IronCache(token=self.token, project_id=self.project_id)
        else:
            self.client = None
        self.memory_cache = {}
        self.key_registry = set()  # Simulasi list_keys jika IronCache tidak support

    async def get(self, key: str) -> Optional[Any]:
        try:
            if self.iron_available and self.client is not None:
                item = self.client.get(self.cache_name, key)
                return json.loads(item.value) if item and item.value else None
            else:
                entry = self.memory_cache.get(key)
                if entry and entry["expires_at"] > datetime.utcnow():
                    return entry["value"]
                return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600, tags: Optional[List[str]] = None):
        try:
            if self.iron_available and self.client is not None:
                self.client.put(self.cache_name, key, json.dumps(value), {"expires_in": ttl})
                self.key_registry.add(key)
            else:
                self.memory_cache[key] = {
                    "value": value,
                    "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
                }
                self.key_registry.add(key)
        except Exception as e:
            print(f"Cache set error: {e}")

    async def delete(self, key: str):
        try:
            if self.iron_available and self.client is not None:
                self.client.delete(self.cache_name, key)
            else:
                self.memory_cache.pop(key, None)
        except Exception as e:
            print(f"Cache delete error: {e}")

    def list_keys(self):
        if self.iron_available and hasattr(self.client, "list_keys"):
            return self.client.list_keys(self.cache_name)
        else:
            return list(self.key_registry)

    async def invalidate_by_tag(self, tag: str):
        """
        Invalidate cache by tag (simulasi: hapus key yang mengandung tag, IronCache tidak support tag native)
        """
        keys = self.list_keys()
        for key in keys:
            if tag in key:
                if self.iron_available and self.client is not None:
                    self.client.delete(self.cache_name, key)
                else:
                    self.memory_cache.pop(key, None)
                    self.key_registry.discard(key)

    async def clear_all(self):
        keys = self.list_keys()
        for key in keys:
            if self.iron_available and self.client is not None:
                self.client.delete(self.cache_name, key)
            else:
                self.memory_cache.pop(key, None)
                self.key_registry.discard(key)

cache_manager = CacheManager()

class LoadBalancer:
    """Simple load balancer implementation"""
    
    def __init__(self):
        self.services = {}
        self.current_index = {}
        self.active_connections = {}  # {service_name: {instance: count}}
    
    def register_service(self, service_name: str, instances: List[str], algorithm: str = "round_robin"):
        """Register a service with load balancer"""
        self.services[service_name] = {
            "instances": instances,
            "algorithm": algorithm,
            "current_index": 0,
            "health_status": {instance: True for instance in instances}
        }
        self.active_connections[service_name] = {instance: 0 for instance in instances}
    
    def get_next_instance(self, service_name: str) -> Optional[str]:
        """Get next available instance"""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        instances = service["instances"]
        
        if not instances:
            return None
        
        if service["algorithm"] == "round_robin":
            # Round robin
            instance = instances[service["current_index"]]
            service["current_index"] = (service["current_index"] + 1) % len(instances)
            self.active_connections[service_name][instance] += 1
            return instance
        
        elif service["algorithm"] == "least_connections":
            # Pilih instance dengan koneksi aktif paling sedikit
            min_instance = min(self.active_connections[service_name], key=self.active_connections[service_name].get)
            self.active_connections[service_name][min_instance] += 1
            return min_instance
        
        else:
            instance = instances[0]
            self.active_connections[service_name][instance] += 1
            return instance
    
    def release_instance(self, service_name: str, instance: str):
        if service_name in self.active_connections and instance in self.active_connections[service_name]:
            self.active_connections[service_name][instance] = max(0, self.active_connections[service_name][instance] - 1)
    
    async def health_check(self, service_name: str):
        """Perform health check on service instances"""
        if service_name not in self.services:
            return
        
        service = self.services[service_name]
        
        for instance in service["instances"]:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(instance)
                    service["health_status"][instance] = resp.status_code == 200
            except Exception as e:
                service["health_status"][instance] = False
                print(f"Health check failed for {instance}: {e}")

load_balancer = LoadBalancer()

# NOTE: Middleware FastAPI hanya bisa didaftarkan di objek FastAPI utama (app), bukan di APIRouter.
# Jika ingin tracking performance, pindahkan logic middleware ke main.py atau server.py pada objek app.

@router.get("/performance/metrics")
async def get_performance_metrics(
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    days: int = Query(7, description="Number of days to analyze"),
    user=Depends(get_current_user)
):
    """
    Get performance metrics
    """
    try:
        from src.db import supabase
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = supabase.table("performance_metrics").select("*").gte("timestamp", start_date.isoformat())
        
        if endpoint:
            query = query.eq("endpoint", endpoint)
        
        if method:
            query = query.eq("method", method)
        
        res = query.order("timestamp", desc=True).execute()
        
        metrics = res.data
        
        if not metrics:
            return {
                "success": True,
                "metrics": [],
                "summary": {
                    "total_requests": 0,
                    "average_response_time": 0,
                    "error_rate": 0
                }
            }
        
        # Calculate summary statistics
        total_requests = len(metrics)
        total_response_time = sum(m["response_time"] for m in metrics)
        average_response_time = total_response_time / total_requests
        
        error_requests = len([m for m in metrics if m["status_code"] >= 400])
        error_rate = (error_requests / total_requests) * 100
        
        # Group by endpoint
        endpoint_stats = {}
        for metric in metrics:
            ep = metric["endpoint"]
            if ep not in endpoint_stats:
                endpoint_stats[ep] = {
                    "requests": 0,
                    "total_time": 0,
                    "errors": 0,
                    "methods": {}
                }
            
            endpoint_stats[ep]["requests"] += 1
            endpoint_stats[ep]["total_time"] += metric["response_time"]
            
            if metric["status_code"] >= 400:
                endpoint_stats[ep]["errors"] += 1
            
            method = metric["method"]
            if method not in endpoint_stats[ep]["methods"]:
                endpoint_stats[ep]["methods"][method] = 0
            endpoint_stats[ep]["methods"][method] += 1
        
        # Calculate averages for endpoints
        for ep in endpoint_stats:
            stats = endpoint_stats[ep]
            stats["average_time"] = stats["total_time"] / stats["requests"]
            stats["error_rate"] = (stats["errors"] / stats["requests"]) * 100
        
        return {
            "success": True,
            "metrics": metrics[:100],  # Limit to recent 100
            "summary": {
                "total_requests": total_requests,
                "average_response_time": average_response_time,
                "error_rate": error_rate,
                "period_days": days
            },
            "endpoint_breakdown": endpoint_stats,
            "period": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.post("/cache/set")
async def set_cache(
    config: CacheConfig,
    user=Depends(get_current_user)
):
    """
    Set value in cache
    """
    try:
        await cache_manager.set(config.key, config.value, config.ttl, config.tags)
        
        return {
            "success": True,
            "key": config.key,
            "ttl": config.ttl,
            "message": "Value cached successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set cache: {str(e)}")

@router.get("/cache/get/{key}")
async def get_cache(
    key: str,
    user=Depends(get_current_user)
):
    """
    Get value from cache
    """
    try:
        value = await cache_manager.get(key)
        
        if value is None:
            raise HTTPException(status_code=404, detail="Key not found in cache")
        
        return {
            "success": True,
            "key": key,
            "value": value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache: {str(e)}")

@router.delete("/cache/delete/{key}")
async def delete_cache(
    key: str,
    user=Depends(get_current_user)
):
    """
    Delete value from cache
    """
    try:
        await cache_manager.delete(key)
        
        return {
            "success": True,
            "key": key,
            "message": "Cache entry deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cache: {str(e)}")

@router.post("/cache/invalidate/tag/{tag}")
async def invalidate_cache_by_tag(
    tag: str,
    user=Depends(get_current_user)
):
    """
    Invalidate all cache entries with specific tag
    """
    try:
        await cache_manager.invalidate_by_tag(tag)
        
        return {
            "success": True,
            "tag": tag,
            "message": f"All cache entries with tag '{tag}' invalidated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(user=Depends(get_current_user)):
    """
    Clear all cache
    """
    try:
        await cache_manager.clear_all()
        
        return {
            "success": True,
            "message": "All cache cleared successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/cache/status")
async def get_cache_status(user=Depends(get_current_user)):
    """
    Get cache status and statistics
    """
    try:
        if cache_manager.iron_available:
            return {
                "success": True,
                "cache_type": "ironcache",
                "status": "available",
                "cache_name": cache_manager.cache_name
            }
        else:
            return {
                "success": True,
                "cache_type": "memory",
                "status": "available",
                "keys_count": len(memory_cache),
                "memory_usage": "unknown",
                "uptime": 0
            }
    except Exception as e:
        return {
            "success": False,
            "cache_type": "none",
            "status": "unavailable",
            "error": str(e)
        }

@router.post("/loadbalancer/register")
async def register_load_balancer_service(
    config: LoadBalancerConfig,
    user=Depends(get_current_user)
):
    """
    Register a service with load balancer
    """
    try:
        load_balancer.register_service(
            config.service_name,
            config.instances,
            config.load_balancing_algorithm
        )
        
        return {
            "success": True,
            "service_name": config.service_name,
            "instances": config.instances,
            "algorithm": config.load_balancing_algorithm,
            "message": "Service registered with load balancer"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register service: {str(e)}")

@router.get("/loadbalancer/instance/{service_name}")
async def get_load_balancer_instance(
    service_name: str,
    user=Depends(get_current_user)
):
    """
    Get next available instance for a service
    """
    try:
        instance = load_balancer.get_next_instance(service_name)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Service not found or no instances available")
        
        return {
            "success": True,
            "service_name": service_name,
            "instance": instance
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get instance: {str(e)}")

@router.get("/loadbalancer/health/{service_name}")
async def health_check_service(
    service_name: str,
    user=Depends(get_current_user)
):
    """
    Perform health check on service instances
    """
    try:
        await load_balancer.health_check(service_name)
        
        if service_name in load_balancer.services:
            service = load_balancer.services[service_name]
            return {
                "success": True,
                "service_name": service_name,
                "health_status": service["health_status"],
                "healthy_instances": sum(1 for status in service["health_status"].values() if status),
                "total_instances": len(service["health_status"])
            }
        else:
            raise HTTPException(status_code=404, detail="Service not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")

@router.get("/performance/health")
async def performance_health_check(user=Depends(get_current_user)):
    """
    Comprehensive performance health check
    """
    try:
        health_status = {
            "database": "healthy",
            "cache": "healthy" if cache_manager.iron_available else "unavailable",
            "load_balancer": "healthy",
            "overall": "healthy"
        }
        
        # Check database
        try:
            from src.db import supabase
            supabase.table("users").select("id").limit(1).execute()
        except Exception as e:
            health_status["database"] = f"unhealthy: {str(e)}"
            health_status["overall"] = "degraded"
        
        # Check cache
        if cache_manager.iron_available:
            try:
                # Simple check: try to set and get a key
                test_key = "health_check"
                await cache_manager.set(test_key, {"ok": True}, ttl=10)
                value = await cache_manager.get(test_key)
                if not value:
                    raise Exception("IronCache not responding")
            except Exception as e:
                health_status["cache"] = f"unhealthy: {str(e)}"
                health_status["overall"] = "degraded"
        
        return {
            "success": True,
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": {
                "overall": "unhealthy",
                "error": str(e)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Cache decorator for endpoints
def cache_response(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache endpoint responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator 

@router.get("/performance/load_balancer_status")
async def load_balancer_status():
    """
    Get status of all registered services in the load balancer
    """
    try:
        services = load_balancer.services
        status = {}
        for name, svc in services.items():
            status[name] = {
                "instances": svc["instances"],
                "algorithm": svc["algorithm"],
                "current_index": svc["current_index"],
                "health_status": svc["health_status"]
            }
        return {"success": True, "status": status, "message": "Load balancer status"}
    except Exception as e:
        return {"success": False, "status": {}, "message": str(e)}

@router.post("/loadbalancer/release/{service_name}/{instance}")
async def release_load_balancer_instance(service_name: str, instance: str, user=Depends(get_current_user)):
    """
    Release an instance after request is done (for least_connections algorithm)
    """
    try:
        load_balancer.release_instance(service_name, instance)
        return {"success": True, "message": f"Released instance {instance} for service {service_name}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/security/audit")
async def security_audit(user=Depends(get_current_user)):
    """
    Simple security audit: list all endpoints and check for permission decorators
    """
    import inspect
    import sys
    endpoints = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, "__call__") and hasattr(obj, "__name__") and obj.__name__.startswith("get_") or obj.__name__.startswith("post_"):
            endpoints.append({
                "name": obj.__name__,
                "doc": inspect.getdoc(obj),
                "has_permission": "user=Depends(get_current_user)" in inspect.getsource(obj)
            })
    return {"success": True, "endpoints": endpoints} 