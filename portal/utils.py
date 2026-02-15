from django.utils import timezone
from .models import AuditLog


def log_action(action, entity, actor=None, details=None, request=None):
    AuditLog.objects.create(
        actor_user=actor,
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(entity.pk),
        details=details or {},
        ip=request.META.get('REMOTE_ADDR') if request else None,
    )
