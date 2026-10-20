"""Parse the "Stop OpenSRE" message shortcut into the conversation it stops.

Slack lists an app's message shortcuts in every message's hover menu. Used on
any message in a thread, this one stops the turn running there — the same
cancel as the ``stop`` chat command, without posting a message to do it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from config.constants.slack import SLACK_STOP_SHORTCUT_CALLBACK_ID
from gateway.transports.slack.processing.events import slack_conversation_key

_MESSAGE_ACTION_TYPE = "message_action"

# Direct-message channel ids start with "D". Shortcut payloads carry no
# ``channel_type``, and a DM is keyed as one conversation, not one per thread.
_DM_CHANNEL_ID_PREFIX = "D"


@dataclass(frozen=True)
class SlackStopRequest:
    """One use of the Stop shortcut, addressed to the conversation it stops."""

    team_id: str
    user_id: str
    channel_id: str
    message_ts: str
    # The message's thread, or "" for a message with no replies.
    thread_ts: str = ""

    @property
    def is_dm(self) -> bool:
        return self.channel_id.startswith(_DM_CHANNEL_ID_PREFIX)

    @property
    def conversation_key(self) -> str:
        """The key the running turn registered its cancel Event under."""
        return slack_conversation_key(
            team_id=self.team_id,
            channel_id=self.channel_id,
            thread_ts=self.thread_ts or self.message_ts,
            is_dm=self.is_dm,
        )


def parse_stop_shortcut_payload(payload: Mapping[str, Any]) -> SlackStopRequest | None:
    """Return the stop request for a Stop shortcut payload, else ``None``."""
    if payload.get("type") != _MESSAGE_ACTION_TYPE:
        return None
    if payload.get("callback_id") != SLACK_STOP_SHORTCUT_CALLBACK_ID:
        return None
    team = _mapping(payload.get("team"))
    user = _mapping(payload.get("user"))
    channel = _mapping(payload.get("channel"))
    message = _mapping(payload.get("message"))
    team_id = str(team.get("id") or user.get("team_id") or "")
    user_id = str(user.get("id") or "")
    channel_id = str(channel.get("id") or "")
    message_ts = str(message.get("ts") or payload.get("message_ts") or "")
    if not (team_id and user_id and channel_id and message_ts):
        return None
    return SlackStopRequest(
        team_id=team_id,
        user_id=user_id,
        channel_id=channel_id,
        message_ts=message_ts,
        thread_ts=str(message.get("thread_ts") or ""),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["SlackStopRequest", "parse_stop_shortcut_payload"]
