## MODIFIED Requirements

### Requirement: Push to purchase with stock check
The system SHALL check stock availability before pushing warehouse items to purchase.

Stock insufficient conditions:
- Stock quantity < Order quantity
- OR Stock quantity ≤ min_stock (low stock threshold)

#### Scenario: Direct shipping item always needs push
- **WHEN** item shipping_method is direct
- **THEN** item is always eligible for push to purchase

#### Scenario: Warehouse item with sufficient stock
- **WHEN** item shipping_method is warehouse and stock quantity >= order quantity and stock > min_stock
- **THEN** item is NOT eligible for push to purchase

#### Scenario: Warehouse item with insufficient stock
- **WHEN** item shipping_method is warehouse and (stock < order quantity OR stock ≤ min_stock)
- **THEN** item is eligible for push to purchase

### Requirement: Display stock info in order detail
The system SHALL display real-time stock information for warehouse items in order detail.

#### Scenario: Show stock quantity
- **WHEN** user views order detail
- **THEN** system shows stock quantity for each warehouse item

#### Scenario: Show push eligibility
- **WHEN** user views order detail
- **THEN** system indicates which items need push to purchase based on stock check

### Requirement: Update order status after push
The system SHALL update sales order status based on push completion.

#### Scenario: Partial push
- **WHEN** user pushes some items to purchase
- **THEN** system updates order_status to partially_pushed_to_purchase

#### Scenario: Full push
- **WHEN** all items needing push are pushed
- **THEN** system updates order_status to pushed_to_purchase