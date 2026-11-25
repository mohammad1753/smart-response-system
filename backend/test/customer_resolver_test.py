
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas.message_processing import (
    NormalizedIncomingMessage,
    StoredMessageType,
)
from app.services.message_processing.customer_resolver import (
    CustomerResolver,
)
from app.services.message_processing.exceptions import (
    ChannelAccountNotFoundError,
    ChannelPlatformMismatchError,
    InactiveChannelAccountError,
)


class FakeSession:

    @contextmanager
    def begin_nested(self):
        yield


class FakeChannelAccountRepository:

    def __init__(self):
        self.context = (
            SimpleNamespace(
                id=10,
                workspace_id=100,
                is_active=True,
            ),
            "rubika",
        )

    def get_with_channel_code(self, session, channel_account_id):
        return self.context


class FakeCustomerRepository:

    def __init__(self):
        self.records = {}
        self.next_id = 1

    def add(self, session, customer):
        customer.id = self.next_id
        self.next_id += 1
        self.records[customer.id] = customer
        return customer

    def get_by_id_and_workspace(
        self,
        session,
        customer_id,
        workspace_id,
    ):
        customer = self.records.get(customer_id)

        if customer is None:
            return None

        if customer.workspace_id != workspace_id:
            return None

        return customer


class FakeCustomerIdentityRepository:

    def __init__(self):
        self.records = {}
        self.next_id = 1

    def get_by_external_user(
        self,
        session,
        channel_account_id,
        external_user_id,
        *,
        for_update=False,
    ):
        return self.records.get(
            (channel_account_id, external_user_id)
        )

    def add(self, session, identity):
        identity.id = self.next_id
        self.next_id += 1

        key = (
            identity.channel_account_id,
            identity.external_user_id,
        )

        self.records[key] = identity

        return identity


def build_message(
    external_user_id="user_123",
    platform="rubika",
):
    now = datetime.now(timezone.utc)

    return NormalizedIncomingMessage(
        channel_account_id=10,
        platform=platform,
        external_message_id="message_123",
        external_chat_id="chat_456",
        external_user_id=external_user_id,
        content="سلام",
        message_type=StoredMessageType.TEXT,
        occurred_at=now,
        received_at=now,
    )


def build_resolver(account_repo, customer_repo, identity_repo):
    return CustomerResolver(
        channel_account_repository=account_repo,
        customer_repository=customer_repo,
        customer_identity_repository=identity_repo,
    )


def test_create_customer():
    account_repo = FakeChannelAccountRepository()
    customer_repo = FakeCustomerRepository()
    identity_repo = FakeCustomerIdentityRepository()

    resolver = build_resolver(
        account_repo,
        customer_repo,
        identity_repo,
    )

    result = resolver.resolve(FakeSession(), build_message())

    assert result.workspace_id == 100
    assert result.channel_account_id == 10
    assert result.customer_id == 1
    assert result.customer_identity_id == 1
    assert result.customer_created is True
    assert result.identity_created is True

    print("New customer creation: PASS")


def test_reuse_existing_customer():
    account_repo = FakeChannelAccountRepository()
    customer_repo = FakeCustomerRepository()
    identity_repo = FakeCustomerIdentityRepository()

    resolver = build_resolver(
        account_repo,
        customer_repo,
        identity_repo,
    )

    session = FakeSession()

    first = resolver.resolve(session, build_message())

    second = resolver.resolve(
        session,
        build_message(external_user_id="user_123"),
    )

    assert first.customer_id == second.customer_id
    assert first.customer_identity_id == second.customer_identity_id
    assert second.customer_created is False
    assert second.identity_created is False

    print("Existing customer reuse: PASS")


def test_platform_mismatch():
    account_repo = FakeChannelAccountRepository()
    customer_repo = FakeCustomerRepository()
    identity_repo = FakeCustomerIdentityRepository()

    resolver = build_resolver(
        account_repo,
        customer_repo,
        identity_repo,
    )

    try:
        resolver.resolve(
            FakeSession(),
            build_message(platform="eitaa"),
        )
    except ChannelPlatformMismatchError:
        print("Platform mismatch protection: PASS")
    else:
        raise AssertionError("Platform mismatch was accepted.")


def test_inactive_account():
    account_repo = FakeChannelAccountRepository()
    account_repo.context[0].is_active = False

    resolver = build_resolver(
        account_repo,
        FakeCustomerRepository(),
        FakeCustomerIdentityRepository(),
    )

    try:
        resolver.resolve(FakeSession(), build_message())
    except InactiveChannelAccountError:
        print("Inactive account protection: PASS")
    else:
        raise AssertionError("Inactive account was accepted.")


def test_missing_account():
    account_repo = FakeChannelAccountRepository()
    account_repo.context = None

    resolver = build_resolver(
        account_repo,
        FakeCustomerRepository(),
        FakeCustomerIdentityRepository(),
    )

    try:
        resolver.resolve(FakeSession(), build_message())
    except ChannelAccountNotFoundError:
        print("Missing account protection: PASS")
    else:
        raise AssertionError("Missing account was accepted.")


if __name__ == "__main__":
    test_create_customer()
    test_reuse_existing_customer()
    test_platform_mismatch()
    test_inactive_account()
    test_missing_account()

    print("\nAll customer resolver tests passed.")




# python -c "import runpy; runpy.run_path('test/customer_resolver_test.py', run_name='__main__')"