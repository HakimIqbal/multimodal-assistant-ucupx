from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import uuid
from api.auth.auth_middleware import get_current_user

router = APIRouter()

class CostEntry(BaseModel):
    id: Optional[str] = None
    user_id: str
    service: str  # groq, gemini, openrouter, etc.
    model: str
    operation: str  # chat, completion, embedding, etc.
    tokens_used: int
    cost_per_token: float
    total_cost: float
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CostAlert(BaseModel):
    id: Optional[str] = None
    user_id: str
    alert_type: str  # daily_limit, monthly_limit, usage_spike
    threshold: float
    current_usage: float
    is_active: bool = True
    created_at: Optional[str] = None

class CostBudget(BaseModel):
    id: Optional[str] = None
    user_id: str
    budget_type: str  # daily, weekly, monthly
    amount: float
    currency: str = "USD"
    start_date: str
    end_date: Optional[str] = None
    is_active: bool = True

# Cost per token for different models (example rates)
MODEL_COSTS = {
    "groq": {
        "llama3-8b-8192": {"input": 0.00000005, "output": 0.00000025},
        "llama3-70b-8192": {"input": 0.00000059, "output": 0.00000247},
        "mixtral-8x7b-32768": {"input": 0.00000014, "output": 0.00000056},
        "gemma2-9b-it": {"input": 0.00000010, "output": 0.00000050}
    },
    "gemini": {
        "gemini-pro": {"input": 0.00000050, "output": 0.00000150},
        "gemini-pro-vision": {"input": 0.00000250, "output": 0.00000750}
    },
    "openrouter": {
        "gpt-4": {"input": 0.00003000, "output": 0.00006000},
        "gpt-3.5-turbo": {"input": 0.00000150, "output": 0.00000200},
        "claude-3-opus": {"input": 0.00001500, "output": 0.00007500},
        "claude-3-sonnet": {"input": 0.00000300, "output": 0.00001500}
    }
}

def calculate_cost(service: str, model: str, input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """Calculate cost for API usage"""
    try:
        service_costs = MODEL_COSTS.get(service, {})
        model_costs = service_costs.get(model, {"input": 0.000001, "output": 0.000002})
        
        input_cost = input_tokens * model_costs["input"]
        output_cost = output_tokens * model_costs["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "cost_per_input_token": model_costs["input"],
            "cost_per_output_token": model_costs["output"]
        }
    except Exception as e:
        print(f"Error calculating cost: {e}")
        return {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
            "cost_per_input_token": 0.0,
            "cost_per_output_token": 0.0
        }

@router.post("/costs/track")
async def track_cost_usage(
    service: str,
    model: str,
    operation: str,
    input_tokens: int,
    output_tokens: int,
    user=Depends(get_current_user)
):
    """
    Track API usage cost
    """
    try:
        from src.db import supabase
        
        # Calculate cost
        cost_info = calculate_cost(service, model, input_tokens, output_tokens)
        
        # Create cost entry
        cost_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "service": service,
            "model": model,
            "operation": operation,
            "tokens_used": input_tokens + output_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_per_token": cost_info["cost_per_input_token"],
            "total_cost": cost_info["total_cost"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "input_cost": cost_info["input_cost"],
                "output_cost": cost_info["output_cost"],
                "cost_per_output_token": cost_info["cost_per_output_token"]
            }
        }
        
        # Save to database
        supabase.table("cost_tracking").insert(cost_entry).execute()
        
        # Check for alerts
        await check_cost_alerts(user["id"], cost_info["total_cost"])
        
        return {
            "success": True,
            "cost_entry_id": cost_entry["id"],
            "cost_breakdown": cost_info,
            "message": "Cost tracked successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track cost: {str(e)}")

@router.get("/costs/summary")
async def get_cost_summary(
    period: str = Query("month", description="Period: day, week, month, year"),
    user=Depends(get_current_user)
):
    """
    Get cost summary for user
    """
    try:
        from src.db import supabase
        
        # Calculate date range
        now = datetime.utcnow()
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=30)
        
        # Get cost entries for period
        res = supabase.table("cost_tracking").select("*").eq("user_id", user["id"]).gte("timestamp", start_date.isoformat()).execute()
        
        cost_entries = res.data
        
        # Calculate summary
        total_cost = sum(entry["total_cost"] for entry in cost_entries)
        total_tokens = sum(entry["tokens_used"] for entry in cost_entries)
        
        # Group by service
        service_costs = {}
        for entry in cost_entries:
            service = entry["service"]
            if service not in service_costs:
                service_costs[service] = {
                    "total_cost": 0,
                    "total_tokens": 0,
                    "operations": 0,
                    "models": {}
                }
            
            service_costs[service]["total_cost"] += entry["total_cost"]
            service_costs[service]["total_tokens"] += entry["tokens_used"]
            service_costs[service]["operations"] += 1
            
            # Track model usage
            model = entry["model"]
            if model not in service_costs[service]["models"]:
                service_costs[service]["models"][model] = {
                    "cost": 0,
                    "tokens": 0,
                    "operations": 0
                }
            
            service_costs[service]["models"][model]["cost"] += entry["total_cost"]
            service_costs[service]["models"][model]["tokens"] += entry["tokens_used"]
            service_costs[service]["models"][model]["operations"] += 1
        
        # Group by operation type
        operation_costs = {}
        for entry in cost_entries:
            operation = entry["operation"]
            if operation not in operation_costs:
                operation_costs[operation] = {
                    "total_cost": 0,
                    "total_tokens": 0,
                    "operations": 0
                }
            
            operation_costs[operation]["total_cost"] += entry["total_cost"]
            operation_costs[operation]["total_tokens"] += entry["tokens_used"]
            operation_costs[operation]["operations"] += 1
        
        # Daily breakdown
        daily_costs = {}
        for entry in cost_entries:
            date = entry["timestamp"][:10]  # YYYY-MM-DD
            if date not in daily_costs:
                daily_costs[date] = 0
            daily_costs[date] += entry["total_cost"]
        
        return {
            "success": True,
            "period": period,
            "summary": {
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "average_cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
                "total_operations": len(cost_entries)
            },
            "service_breakdown": service_costs,
            "operation_breakdown": operation_costs,
            "daily_breakdown": daily_costs,
            "period_start": start_date.isoformat(),
            "period_end": now.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")

@router.get("/costs/forecast")
async def get_cost_forecast(
    days: int = Query(30, description="Number of days to forecast"),
    user=Depends(get_current_user)
):
    """
    Forecast future costs based on current usage patterns
    """
    try:
        from src.db import supabase
        
        # Get recent usage data (last 30 days)
        start_date = datetime.utcnow() - timedelta(days=30)
        res = supabase.table("cost_tracking").select("*").eq("user_id", user["id"]).gte("timestamp", start_date.isoformat()).execute()
        
        cost_entries = res.data
        
        if not cost_entries:
            return {
                "success": True,
                "forecast": {
                    "daily_average": 0,
                    "monthly_forecast": 0,
                    "confidence": "low"
                }
            }
        
        # Calculate daily averages
        daily_costs = {}
        for entry in cost_entries:
            date = entry["timestamp"][:10]
            if date not in daily_costs:
                daily_costs[date] = 0
            daily_costs[date] += entry["total_cost"]
        
        # Calculate average daily cost
        total_days = len(daily_costs)
        total_cost = sum(daily_costs.values())
        daily_average = total_cost / total_days if total_days > 0 else 0
        
        # Forecast
        monthly_forecast = daily_average * 30
        forecast_period = daily_average * days
        
        # Confidence level based on data consistency
        if total_days >= 20:
            confidence = "high"
        elif total_days >= 10:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Trend analysis
        recent_days = sorted(daily_costs.items())[-7:]  # Last 7 days
        if len(recent_days) >= 2:
            recent_avg = sum(cost for _, cost in recent_days) / len(recent_days)
            trend = "increasing" if recent_avg > daily_average else "decreasing" if recent_avg < daily_average else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "success": True,
            "forecast": {
                "daily_average": daily_average,
                "monthly_forecast": monthly_forecast,
                f"{days}_day_forecast": forecast_period,
                "confidence": confidence,
                "trend": trend,
                "data_points": total_days
            },
            "historical_data": {
                "total_days_analyzed": total_days,
                "total_cost_analyzed": total_cost,
                "daily_breakdown": daily_costs
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

@router.post("/costs/alerts")
async def create_cost_alert(
    alert: CostAlert,
    user=Depends(get_current_user)
):
    """
    Create a cost alert
    """
    try:
        from src.db import supabase
        
        alert_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "alert_type": alert.alert_type,
            "threshold": alert.threshold,
            "current_usage": alert.current_usage,
            "is_active": alert.is_active,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("cost_alerts").insert(alert_data).execute()
        
        return {
            "success": True,
            "alert_id": alert_data["id"],
            "message": "Cost alert created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")

@router.get("/costs/alerts")
async def get_cost_alerts(user=Depends(get_current_user)):
    """
    Get user's cost alerts
    """
    try:
        from src.db import supabase
        
        res = supabase.table("cost_alerts").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "alerts": res.data,
            "total_alerts": len(res.data),
            "active_alerts": len([a for a in res.data if a["is_active"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/costs/budgets")
async def create_cost_budget(
    budget: CostBudget,
    user=Depends(get_current_user)
):
    """
    Create a cost budget
    """
    try:
        from src.db import supabase
        
        budget_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "budget_type": budget.budget_type,
            "amount": budget.amount,
            "currency": budget.currency,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "is_active": budget.is_active,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("cost_budgets").insert(budget_data).execute()
        
        return {
            "success": True,
            "budget_id": budget_data["id"],
            "message": "Cost budget created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create budget: {str(e)}")

@router.get("/costs/budgets")
async def get_cost_budgets(user=Depends(get_current_user)):
    """
    Get user's cost budgets
    """
    try:
        from src.db import supabase
        
        res = supabase.table("cost_budgets").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        
        # Calculate current usage for each budget
        budgets = []
        for budget in res.data:
            # Get usage for budget period
            usage_query = supabase.table("cost_tracking").select("total_cost").eq("user_id", user["id"]).gte("timestamp", budget["start_date"])
            if budget["end_date"]:
                usage_query = usage_query.lte("timestamp", budget["end_date"])
            usage_res = usage_query.execute()
            current_usage = sum(entry["total_cost"] for entry in usage_res.data)
            remaining_budget = budget["amount"] - current_usage
            
            budgets.append({
                **budget,
                "current_usage": current_usage,
                "remaining_budget": remaining_budget,
                "usage_percentage": (current_usage / budget["amount"]) * 100 if budget["amount"] > 0 else 0
            })
        
        return {
            "success": True,
            "budgets": budgets,
            "total_budgets": len(budgets),
            "active_budgets": len([b for b in budgets if b["is_active"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get budgets: {str(e)}")

@router.get("/costs/models")
async def get_model_costs(user=Depends(get_current_user)):
    """
    Get cost information for all available models
    """
    try:
        return {
            "success": True,
            "model_costs": MODEL_COSTS,
            "currency": "USD",
            "note": "Costs are per token and may vary based on usage volume"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model costs: {str(e)}")

async def check_cost_alerts(user_id: str, current_cost: float):
    """Check if any cost alerts should be triggered"""
    try:
        from src.db import supabase
        
        # Get user's active alerts
        alerts_res = supabase.table("cost_alerts").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        
        for alert in alerts_res.data:
            if current_cost >= alert["threshold"]:
                # Trigger alert (in production, send notification)
                print(f"Cost alert triggered for user {user_id}: {alert['alert_type']} threshold exceeded")
                
                # Update alert
                supabase.table("cost_alerts").update({
                    "current_usage": current_cost,
                    "triggered_at": datetime.utcnow().isoformat()
                }).eq("id", alert["id"]).execute()
                
    except Exception as e:
        print(f"Error checking cost alerts: {e}") 