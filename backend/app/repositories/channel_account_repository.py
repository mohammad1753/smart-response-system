
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.channel_account import ChannelAccount


class ChannelAccountRepository:
    """Database operations for channel accounts."""

    def get_with_channel_code(
        self,
        session: Session,
        channel_account_id: int,
    ) -> tuple[ChannelAccount, str] | None:

        statement = (
            select(ChannelAccount, Channel.code)
            .join(
                Channel,
                Channel.id == ChannelAccount.channel_id,
            )
            .where(ChannelAccount.id == channel_account_id)
        )

        row = session.execute(statement).one_or_none()

        if row is None:
            return None

        account, channel_code = row

        return account, str(channel_code)
