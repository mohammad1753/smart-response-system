
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    """Database operations for customers."""

    def get_by_id_and_workspace(
        self,
        session: Session,
        customer_id: int,
        workspace_id: int,
    ) -> Customer | None:

        statement = select(Customer).where(
            Customer.id == customer_id,
            Customer.workspace_id == workspace_id,
        )

        return session.scalar(statement)

    def add(
        self,
        session: Session,
        customer: Customer,
    ) -> Customer:

        session.add(customer)
        session.flush()

        return customer
