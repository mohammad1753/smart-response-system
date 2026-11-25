
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_identity import CustomerIdentity


class CustomerIdentityRepository:
    """Database operations for customer identities."""

    def get_by_external_user(
        self,
        session: Session,
        channel_account_id: int,
        external_user_id: str,
        *,
        for_update: bool = False,
    ) -> CustomerIdentity | None:

        statement = select(CustomerIdentity).where(
            CustomerIdentity.channel_account_id == channel_account_id,
            CustomerIdentity.external_user_id == external_user_id,
        )

        if for_update:
            statement = statement.with_for_update()

        return session.scalar(statement)

    def add(
        self,
        session: Session,
        identity: CustomerIdentity,
    ) -> CustomerIdentity:

        session.add(identity)
        session.flush()

        return identity
