
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

    def get_for_update(
        self,
        session: Session,
        identity_id: int,
        customer_id: int,
        channel_account_id: int,
        workspace_id: int,
    ) -> CustomerIdentity | None:
        """Lock and retrieve a customer identity within its scope."""

        statement = (
            select(CustomerIdentity)
            .where(
                CustomerIdentity.id == identity_id,
                CustomerIdentity.customer_id == customer_id,
                CustomerIdentity.channel_account_id == channel_account_id,
                CustomerIdentity.workspace_id == workspace_id,
            )
            .with_for_update()
        )

        return session.scalar(statement)
