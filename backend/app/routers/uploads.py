"""Upload route guards for RBAC testing until full upload is implemented.

Exposes analyst-only upload and admin-only delete endpoints that validate
permissions without processing files. Replaced by upload service in Task 7.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin, require_analyst
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/guard", summary="Analyst upload permission check")
def upload_permission_check(
    _: Annotated[User, Depends(require_analyst)],
) -> dict[str, bool]:
    """Verify the caller may upload files (analyst or admin)."""
    return {"allowed": True}


@router.delete("/guard", summary="Admin delete permission check")
def delete_permission_check(
    _: Annotated[User, Depends(require_admin)],
) -> dict[str, bool]:
    """Verify the caller may delete files (admin only)."""
    return {"allowed": True}
