## ADDED Requirements

### Requirement: Order pending status
The system SHALL support pending status for sales orders awaiting approval.

#### Scenario: Submit order for approval
- **WHEN** user submits a draft sales order
- **THEN** system changes order_status from draft to pending

#### Scenario: Approve pending order
- **WHEN** user approves a pending sales order
- **THEN** system changes order_status from pending to audited

#### Scenario: Reject pending order
- **WHEN** user rejects a pending sales order
- **THEN** system changes order_status from pending to draft

### Requirement: Create and approve shortcut
The system SHALL support creating and approving sales order in one action.

#### Scenario: Create and approve order
- **WHEN** user creates order with submit=True parameter
- **THEN** system creates order with order_status directly set to audited

### Requirement: Order status flow recording
The system SHALL record all status changes in order_status_flows table.

#### Scenario: Record status change
- **WHEN** order status changes
- **THEN** system creates a flow record with old_value, new_value, operator, and operate_time