from typing import Dict, Any

from django.http import HttpRequest

from students.models import Student


def user_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Provide common user-related context to all templates so layout components
    (sidebar, top bar) can render consistently across views.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    if user.is_superuser or user.is_staff:
        role = "admin"
    elif hasattr(user, "teacher"):
        role = "teacher"
    elif hasattr(user, "student"):
        role = "student"
    else:
        role = None

    context = {"role": role}

    if role == "admin":
        context["total_students"] = Student.objects.count()

    return context
