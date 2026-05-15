## MODIFIED Requirements

### Requirement: Order status transitions
The system SHALL enforce valid status transitions for sales orders.

Valid transitions:
- draft → pending (submit)
- draft → cancelled (cancel)
- pending → audited (approve)
- pending → draft (reject)
- audited → partially_pushed_to_purchase (partial push)
- audited → pushed_to_purchase (full push)
- partially_pushed_to_purchase → pushed_to_purchase (continue push)
- partially_pushed_to_purchase → closed (close)
- pushed_to_purchase → closed (close)
- Any status → cancelled (cancel, with restrictions)

#### Scenario: Submit draft order
- **WHEN** user submits a draft order
- **THEN** system changes status to pending

#### Scenario: Reject pending order
- **WHEN** user rejects a pending order
- **THEN** system changes status back to draft

#### Scenario: Invalid status transition
- **WHEN** user attempts invalid status transition
- **THEN** system rejects with error message "订单状态不允许从 {old} 变更为 {new}"