"""Proves the schema constraints from master spec §28 are enforced by the
database itself, not merely documented in code comments.
"""
import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.domain.enums import OrderItemStatus, OrderStatus
from app.models import Drug, Inventory, Order, OrderItem, Patient

# MySQL reports CHECK constraint violations (error 3819) as OperationalError
# rather than IntegrityError; foreign key/unique violations remain IntegrityError.
CONSTRAINT_VIOLATION = (IntegrityError, OperationalError)


def make_drug(db: Session, code: str = "TEST-DRUG-001") -> Drug:
    drug = Drug(code=code, name="Test Drug", strength="500 mg", dosage_form="Tablet")
    db.add(drug)
    db.flush()
    return drug


def make_patient(db: Session) -> Patient:
    patient = Patient(full_name="Test Patient")
    db.add(patient)
    db.flush()
    return patient


def make_order(db: Session, patient: Patient, order_number: str = "ORD-TEST-0001") -> Order:
    order = Order(order_number=order_number, patient_id=patient.id, status=OrderStatus.NEW)
    db.add(order)
    db.flush()
    return order


class TestTablesAndForeignKeys:
    def test_all_core_tables_exist(self, db_session: Session):
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        tables = set(inspector.get_table_names())
        expected = {"patients", "drugs", "inventory", "orders", "order_items", "inventory_transactions"}
        assert expected.issubset(tables)

    def test_inventory_foreign_key_rejects_nonexistent_drug(self, db_session: Session):
        db_session.add(Inventory(drug_id=999_999_999, quantity_on_hand=10, low_stock_threshold=5, reorder_threshold=2))
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()


class TestUniqueConstraints:
    def test_duplicate_drug_code_rejected(self, db_session: Session):
        make_drug(db_session, code="DUP-CODE")
        db_session.add(Drug(code="DUP-CODE", name="Another Name"))
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_duplicate_order_number_rejected(self, db_session: Session):
        patient = make_patient(db_session)
        make_order(db_session, patient, order_number="ORD-DUP-0001")
        db_session.add(Order(order_number="ORD-DUP-0001", patient_id=patient.id, status=OrderStatus.NEW))
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_duplicate_drug_line_in_same_order_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="DUP-LINE-DRUG")
        patient = make_patient(db_session)
        order = make_order(db_session, patient, order_number="ORD-DUP-LINE-0001")

        db_session.add(
            OrderItem(order_id=order.id, drug_id=drug.id, requested_quantity=5, status=OrderItemStatus.PENDING)
        )
        db_session.flush()

        db_session.add(
            OrderItem(order_id=order.id, drug_id=drug.id, requested_quantity=1, status=OrderItemStatus.PENDING)
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()


class TestInventoryCheckConstraints:
    def test_negative_quantity_on_hand_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="NEG-QTY-DRUG")
        db_session.add(
            Inventory(drug_id=drug.id, quantity_on_hand=-1, low_stock_threshold=5, reorder_threshold=2)
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_negative_low_stock_threshold_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="NEG-LOW-THRESH-DRUG")
        db_session.add(
            Inventory(drug_id=drug.id, quantity_on_hand=10, low_stock_threshold=-5, reorder_threshold=2)
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_reorder_threshold_above_low_stock_threshold_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="BAD-THRESHOLD-DRUG")
        db_session.add(
            Inventory(drug_id=drug.id, quantity_on_hand=10, low_stock_threshold=5, reorder_threshold=6)
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_valid_inventory_row_is_accepted(self, db_session: Session):
        drug = make_drug(db_session, code="VALID-INVENTORY-DRUG")
        db_session.add(
            Inventory(drug_id=drug.id, quantity_on_hand=100, low_stock_threshold=20, reorder_threshold=5)
        )
        db_session.flush()  # should not raise


class TestOrderItemCheckConstraints:
    def test_zero_requested_quantity_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="ZERO-QTY-DRUG")
        patient = make_patient(db_session)
        order = make_order(db_session, patient, order_number="ORD-ZERO-QTY-0001")
        db_session.add(
            OrderItem(order_id=order.id, drug_id=drug.id, requested_quantity=0, status=OrderItemStatus.PENDING)
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_negative_requested_quantity_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="NEG-QTY-ITEM-DRUG")
        patient = make_patient(db_session)
        order = make_order(db_session, patient, order_number="ORD-NEG-QTY-0001")
        db_session.add(
            OrderItem(order_id=order.id, drug_id=drug.id, requested_quantity=-5, status=OrderItemStatus.PENDING)
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()

    def test_negative_dispensed_quantity_rejected(self, db_session: Session):
        drug = make_drug(db_session, code="NEG-DISPENSED-DRUG")
        patient = make_patient(db_session)
        order = make_order(db_session, patient, order_number="ORD-NEG-DISPENSED-0001")
        db_session.add(
            OrderItem(
                order_id=order.id,
                drug_id=drug.id,
                requested_quantity=10,
                dispensed_quantity=-1,
                status=OrderItemStatus.PENDING,
            )
        )
        with pytest.raises(CONSTRAINT_VIOLATION):
            db_session.flush()
