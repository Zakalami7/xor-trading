"""XOR Trading Platform - Exchange Routes"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import encrypt_api_key
from ...db.session import get_db
from ...models.api_credential import APICredential
from ...models.user import User
from ...schemas.bot import APICredentialCreate, APICredentialResponse
from ..deps import get_current_user

router = APIRouter()

SUPPORTED_EXCHANGES = ["binance", "bybit", "okx", "kraken"]


@router.get("/supported")
async def list_supported_exchanges():
    """List supported exchanges."""
    return {
        "exchanges": [
            {"id": "binance", "name": "Binance", "spot": True, "futures": True},
            {"id": "bybit", "name": "Bybit", "spot": True, "futures": True},
            {"id": "okx", "name": "OKX", "spot": True, "futures": True},
            {"id": "kraken", "name": "Kraken", "spot": True, "futures": False},
        ]
    }


@router.get("/credentials", response_model=List[APICredentialResponse])
async def list_credentials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's exchange API credentials."""
    query = select(APICredential).where(
        APICredential.user_id == current_user.id,
        APICredential.deleted_at.is_(None),
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/credentials", response_model=APICredentialResponse, status_code=201)
async def create_credential(
    credential: APICredentialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new exchange API credential."""
    if credential.exchange not in SUPPORTED_EXCHANGES:
        raise HTTPException(status_code=400, detail="Unsupported exchange")
    
    # Encrypt API keys
    api_key_encrypted = encrypt_api_key(credential.api_key, str(current_user.id))
    api_secret_encrypted = encrypt_api_key(credential.api_secret, str(current_user.id))
    passphrase_encrypted = None
    if credential.passphrase:
        passphrase_encrypted = encrypt_api_key(credential.passphrase, str(current_user.id))
    
    cred = APICredential(
        user_id=current_user.id,
        name=credential.name,
        exchange=credential.exchange,
        api_key_encrypted=api_key_encrypted,
        api_secret_encrypted=api_secret_encrypted,
        passphrase_encrypted=passphrase_encrypted,
        api_key_last4=credential.api_key[-4:],
        is_testnet=credential.is_testnet,
    )
    
    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return cred


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API credential."""
    cred = await db.get(APICredential, credential_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    cred.soft_delete()
    await db.commit()
    return {"message": "Credential deleted"}
