
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity

from app.repositories.channel_account_repository import (
    ChannelAccountRepository,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.customer_identity_repository import (
    CustomerIdentityRepository,
)

from app.schemas.message_processing import (
    NormalizedIncomingMessage,
    ResolvedCustomer,
)

from app.services.message_processing.exceptions import (
    ChannelAccountNotFoundError,
    ChannelPlatformMismatchError,
    CustomerIntegrityError,
    InactiveChannelAccountError,
)


class CustomerResolver:
    """Identify or create customers from incoming channel messages."""

    def __init__(
        self,
        channel_account_repository=None,
        customer_repository=None,
        customer_identity_repository=None,
    ) -> None:

        self.channel_accounts = (
            channel_account_repository or ChannelAccountRepository()
        )

        self.customers = (
            customer_repository or CustomerRepository()
        )

        self.identities = (
            customer_identity_repository
            or CustomerIdentityRepository()
        )

    def resolve(
        self,
        session: Session,
        message: NormalizedIncomingMessage,
    ) -> ResolvedCustomer:

        # 1. Resolve the trusted channel account.
        context = self.channel_accounts.get_with_channel_code(
            session,
            message.channel_account_id,
        )

        if context is None:
            raise ChannelAccountNotFoundError(
                "Channel account was not found."
            )

        account, channel_code = context

        # 2. Validate account activation.
        if not account.is_active:
            raise InactiveChannelAccountError(
                "Channel account is inactive."
            )

        # 3. Verify platform consistency.
        if channel_code.strip().casefold() != message.platform.casefold():
            raise ChannelPlatformMismatchError(
                "Incoming message platform does not match "
                "the channel account platform."
            )

        # 4. Look for an existing customer identity.
        identity = self.identities.get_by_external_user(
            session,
            channel_account_id=account.id,
            external_user_id=message.external_user_id,
        )

        if identity is not None:
            return self._build_result(
                session=session,
                account=account,
                identity=identity,
                customer_created=False,
                identity_created=False,
            )

        # 5. Create customer and identity inside a savepoint.
        try:
            with session.begin_nested():

                customer = self.customers.add(
                    session,
                    Customer(
                        workspace_id=account.workspace_id,
                        full_name=None,
                    ),
                )

                identity = self.identities.add(
                    session,
                    CustomerIdentity(
                        workspace_id=account.workspace_id,
                        customer_id=customer.id,
                        channel_account_id=account.id,
                        external_user_id=message.external_user_id,
                        display_name=None,
                    ),
                )

        except IntegrityError:
            # A concurrent transaction may have created
            # this identity after our initial lookup.
            identity = self.identities.get_by_external_user(
                session,
                channel_account_id=account.id,
                external_user_id=message.external_user_id,
                for_update=True,
            )

            if identity is None:
                raise

            return self._build_result(
                session=session,
                account=account,
                identity=identity,
                customer_created=False,
                identity_created=False,
            )

        return self._build_result(
            session=session,
            account=account,
            identity=identity,
            customer_created=True,
            identity_created=True,
        )

    def _build_result(
        self,
        session: Session,
        account,
        identity: CustomerIdentity,
        *,
        customer_created: bool,
        identity_created: bool,
    ) -> ResolvedCustomer:

        if identity.workspace_id != account.workspace_id:
            raise CustomerIntegrityError(
                "Customer identity belongs to an unexpected workspace."
            )

        customer = self.customers.get_by_id_and_workspace(
            session,
            customer_id=identity.customer_id,
            workspace_id=account.workspace_id,
        )

        if customer is None:
            raise CustomerIntegrityError(
                "Customer referenced by identity was not found."
            )

        return ResolvedCustomer(
            workspace_id=account.workspace_id,
            channel_account_id=account.id,
            customer_id=customer.id,
            customer_identity_id=identity.id,
            external_user_id=identity.external_user_id,
            customer_created=customer_created,
            identity_created=identity_created,
        )
