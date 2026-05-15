## ADDED Requirements

### Requirement: Purchase order recall
The system SHALL allow recalling (deleting) purchase orders in draft or audited status.

#### Scenario: Recall draft purchase order
- **WHEN** user recalls a draft purchase order
- **THEN** system deletes the purchase order and updates related sales order

#### Scenario: Recall audited purchase order
- **WHEN** user recalls an audited purchase order
- **THEN** system deletes the purchase order and updates related sales order

### Requirement: Sales order status rollback on recall
The system SHALL rollback sales order status when purchase order is recalled.

#### Scenario: Rollback partially pushed status
- **WHEN** recalling purchase order and sales order was partially_pushed_to_purchase
- **THEN** system recalculates sales order status based on remaining pushed items

#### Scenario: Rollback fully pushed status
- **WHEN** recalling purchase order and all items were pushed
- **THEN** system changes sales order status back to audited

### Requirement: Sales order item pushed flag rollback
The system SHALL reset pushed flag on sales order items when purchase order is recalled.

#### Scenario: Reset pushed flag
- **WHEN** recalling purchase order
- **THEN** system sets pushed=false for all items linked to the recalled purchase order