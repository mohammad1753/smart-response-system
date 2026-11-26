
from sqlalchemy.orm import Session

from app.models.conversation import Conversation

from app.repositories.customer_identity_repository import (
    CustomerIdentityRepository,
)
from app.repositories.conversation_repository import (
    ConversationRepository,
)

from app.schemas.message_processing import (
    ConversationStatus,
    ResolvedCustomer,
    ResolvedConversation,
)

from app.services.message_processing.exceptions import (
    CustomerIdentityNotFoundError,
    ConversationIntegrityError,
)


class ConversationManager:
    """Find or create a conversation for a resolved customer."""

    ACTIVE_STATUSES = (
        ConversationStatus.AI_ACTIVE.value,
        ConversationStatus.HUMAN_REQUIRED.value,
        ConversationStatus.HUMAN_ACTIVE.value,
    )

    def __init__(
        self,
        identity_repository=None,
        conversation_repository=None,
    ) -> None:
        self.identities = (
            identity_repository
            or CustomerIdentityRepository()
        )

        self.conversations = (
            conversation_repository
            or ConversationRepository()
        )

    def resolve_or_create(
        self,
        session: Session,
        customer: ResolvedCustomer,
    ) -> ResolvedConversation:
        """
        Reuse an active conversation or create a new one.

        This method does not commit. The caller owns the transaction.
        """

        # 1. Lock and validate the resolved customer identity.
        identity = self.identities.get_for_update(
            session=session,
            identity_id=customer.customer_identity_id,
            customer_id=customer.customer_id,
            channel_account_id=customer.channel_account_id,
            workspace_id=customer.workspace_id,
        )

        if identity is None:
            raise CustomerIdentityNotFoundError(
                "Resolved customer identity was not found "
                "within its expected scope."
            )

        # 2. Find an existing active conversation.
        existing = self.conversations.get_active_by_identity(
            session=session,
            workspace_id=customer.workspace_id,
            customer_identity_id=customer.customer_identity_id,
            channel_account_id=customer.channel_account_id,
            active_statuses=self.ACTIVE_STATUSES,
        )

        if existing is not None:
            if (
                existing.workspace_id != customer.workspace_id
                or existing.customer_identity_id
                != customer.customer_identity_id
                or existing.channel_account_id
                != customer.channel_account_id
            ):
                raise ConversationIntegrityError(
                    "Existing conversation scope is inconsistent."
                )

            return self._build_result(
                customer=customer,
                conversation=existing,
                created=False,
            )

        # 3. No active conversation exists: create one.
        conversation = Conversation(
            workspace_id=customer.workspace_id,
            customer_identity_id=customer.customer_identity_id,
            channel_account_id=customer.channel_account_id,
            status=ConversationStatus.AI_ACTIVE.value,
        )

        created = self.conversations.add(
            session,
            conversation,
        )

        return self._build_result(
            customer=customer,
            conversation=created,
            created=True,
        )

    @staticmethod
    def _build_result(
        customer: ResolvedCustomer,
        conversation: Conversation,
        *,
        created: bool,
    ) -> ResolvedConversation:

        try:
            status = ConversationStatus(conversation.status)
        except ValueError as exc:
            raise ConversationIntegrityError(
                f"Unsupported conversation status: {conversation.status}"
            ) from exc

        return ResolvedConversation(
            workspace_id=customer.workspace_id,
            channel_account_id=customer.channel_account_id,
            customer_id=customer.customer_id,
            customer_identity_id=customer.customer_identity_id,
            conversation_id=conversation.id,
            status=status,
            conversation_created=created,
        )
