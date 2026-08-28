from fastapi import APIRouter, Query

from app.game.board import Board, generate_board

router = APIRouter(prefix="/board", tags=["board"])


@router.get("", response_model=Board)
async def get_demo_board(player_count: int = Query(4, ge=2, le=6), seed: int | None = None):
    return generate_board(player_count, seed=seed)
