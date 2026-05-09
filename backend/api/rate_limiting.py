"""
Rate limiting utilities for the API.

Provides rate limiting decorators and utilities for protecting
API endpoints from excessive requests.
"""

from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps
from rest_framework import status
from datetime import datetime, timedelta


def rate_limit(max_requests: int, time_window_minutes: int):
    """
    Rate limiting decorator for API views.
    
    Uses Django's cache framework to track requests per user.
    
    Args:
        max_requests: Maximum number of requests allowed
        time_window_minutes: Time window in minutes
    
    Returns:
        A decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get user identifier (authenticated user or IP)
            if request.user and request.user.is_authenticated:
                user_id = f'user_{request.user.id}'
            else:
                user_id = f'ip_{request.META.get("REMOTE_ADDR", "unknown")}'
            
            # Create cache key for this user/endpoint
            cache_key = f'rate_limit_{user_id}_{view_func.__name__}'
            
            # Get current request count
            current_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_count >= max_requests:
                return JsonResponse(
                    {
                        'detail': f'Rate limit exceeded. Maximum {max_requests} requests per {time_window_minutes} minutes.'
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Increment counter and set expiry
            cache.set(
                cache_key,
                current_count + 1,
                timeout=time_window_minutes * 60
            )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def get_rate_limit_status(user_id: int, endpoint: str, max_requests: int, time_window_minutes: int) -> dict:
    """
    Get the current rate limit status for a user on an endpoint.
    
    Args:
        user_id: User ID
        endpoint: Endpoint name/identifier
        max_requests: Maximum allowed requests
        time_window_minutes: Time window in minutes
    
    Returns:
        Dict with current_requests, remaining_requests, reset_time
    """
    cache_key = f'rate_limit_user_{user_id}_{endpoint}'
    current_count = cache.get(cache_key, 0)
    
    return {
        'current_requests': current_count,
        'remaining_requests': max(0, max_requests - current_count),
        'limit': max_requests,
        'reset_seconds': cache.ttl(cache_key) if current_count > 0 else 0,
    }
