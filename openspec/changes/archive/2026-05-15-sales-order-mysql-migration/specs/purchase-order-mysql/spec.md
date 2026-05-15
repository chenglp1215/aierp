## ADDED Requirements

### Requirement: Purchase order MySQL model
The system SHALL store purchase orders in MySQL database using Tortoise ORM with the following structure:
- purchase_orders table for order headers
- purchase_order_items table for order line items (one-to-many relation)

#### Scenario: Create purchase order in MySQL
- **WHEN** system generates purchase order from sales order
- **THEN** system stores order header in purchase_orders table and items in purchase_order_items table

### Requirement: Purchase order generation from sales order
The system SHALL generate purchase orders from sales order items grouped by brand_id.

#### Scenario: Generate purchase orders by brand
- **WHEN** pushing selected items to purchase
- **THEN** system creates one purchase order per brand_id from selected items

#### Scenario: Link purchase order to sales order
- **WHEN** creating purchase order from sales order
- **THEN** system stores source_sale_order_id and source_sale_row_no in purchase order items

### Requirement: Purchase order CRUD operations
The system SHALL provide full CRUD operations for purchase orders using Tortoise ORM.

#### Scenario: List purchase orders with filters
- **WHEN** user requests purchase order list with status or brand_id filter
- **THEN** system returns filtered paginated results

### Requirement: Purchase order status management
The system SHALL manage purchase order status: draft, audited, closed, cancelled.

#### Scenario: Approve purchase order
- **WHEN** user approves a draft purchase order
- **THEN** system updates purchase_status to audited

#### Scenario: Recall purchase order
- **WHEN** user recalls a draft or audited purchase order
- **THEN** system deletes purchase order and updates related sales order status