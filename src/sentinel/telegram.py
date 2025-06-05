"""Telegram bot that exposes the agent pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sentinel.agent.runner import (
        AgentOrchestrator,
    )

log = structlog.get_logger(__name__)


class SentinelBot:
    """Async Telegram bot wrapper.

    Delegates every user message to ``AgentOrchestrator``
    and replies with the answer + sources.
    """

    def __init__(
        self,
        token: str,
        agent: AgentOrchestrator,
    ) -> None:
        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            MessageHandler,
            filters,
        )

        self._agent = agent
        self._app = ApplicationBuilder().token(token).build()
        self._app.add_handler(CommandHandler("start", self._on_start))
        self._app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._on_message,
            )
        )

    async def start(self) -> None:
        """Begin polling for updates."""
        await self._app.initialize()
        await self._app.start()
        if self._app.updater:
            await self._app.updater.start_polling()
        log.info("telegram_polling_started")

    async def stop(self) -> None:
        """Gracefully shut down the bot."""
        if self._app.updater:
            await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()
        log.info("telegram_stopped")

    # -- handlers -------------------------------------------------

    @staticmethod
    async def _on_start(update, context) -> None:  # type: ignore[no-untyped-def]
        await update.message.reply_text(
            "Welcome to arxiv-sentinel!  "
            "Ask me anything about recent AI research."
        )

    async def _on_message(self, update, context) -> None:  # type: ignore[no-untyped-def]
        text = update.message.text
        if not text:
            return
        try:
            result = await self._agent.process_query(text)
            reply = result.answer
            if result.sources:
                reply += "\n\nSources:\n"
                reply += "\n".join(result.sources)
            await update.message.reply_text(reply)
        except Exception:
            log.exception(
                "telegram_handler_error",
                text=text[:80],
            )
            await update.message.reply_text("Sorry, something went wrong.")


def create_sentinel_bot(
    token: str,
    agent: AgentOrchestrator,
) -> SentinelBot:
    """Factory: build a ``SentinelBot``."""
    return SentinelBot(token=token, agent=agent)
