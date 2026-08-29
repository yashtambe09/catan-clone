from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])

MATCH_HISTORY_LIMIT = 20


class StatsSummary(BaseModel):
    games_played: int
    wins: int
    losses: int
    win_rate: float


class MatchHistoryEntry(BaseModel):
    started_at: datetime
    board_size: str
    final_score: int | None
    placement: int | None
    opponents: list[str]
    result: str


class StatsResponse(BaseModel):
    summary: StatsSummary
    matches: list[MatchHistoryEntry]


@router.get("/me", response_model=StatsResponse)
async def my_stats(request: Request, user: dict = Depends(get_current_user)):
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        summary_row = await conn.fetchrow(
            "SELECT COUNT(*) AS games_played, "
            "COUNT(*) FILTER (WHERE placement = 1) AS wins "
            "FROM game_players WHERE user_id = $1",
            user["user_id"],
        )
        match_rows = await conn.fetch(
            "SELECT g.started_at, g.board_size, gp.final_score, gp.placement, "
            "(SELECT array_agg(u2.username ORDER BY u2.username) "
            " FROM game_players gp2 JOIN users u2 ON u2.id = gp2.user_id "
            " WHERE gp2.game_id = g.id AND gp2.user_id != $1) AS opponents "
            "FROM game_players gp JOIN games g ON g.id = gp.game_id "
            "WHERE gp.user_id = $1 "
            "ORDER BY g.started_at DESC LIMIT $2",
            user["user_id"],
            MATCH_HISTORY_LIMIT,
        )

    games_played = summary_row["games_played"]
    wins = summary_row["wins"]
    summary = StatsSummary(
        games_played=games_played,
        wins=wins,
        losses=games_played - wins,
        win_rate=round(100 * wins / games_played, 1) if games_played else 0.0,
    )

    matches = [
        MatchHistoryEntry(
            started_at=row["started_at"],
            board_size=row["board_size"],
            final_score=row["final_score"],
            placement=row["placement"],
            opponents=row["opponents"] or [],
            result="win" if row["placement"] == 1 else "loss",
        )
        for row in match_rows
    ]

    return StatsResponse(summary=summary, matches=matches)
