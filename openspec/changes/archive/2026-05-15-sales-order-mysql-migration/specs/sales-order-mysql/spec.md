## ADDED Requirements

### Requirement: Sales order MySQL model
The system SHALL store sales orders in MySQL database using Tortoise ORM with the following structure:
- sales_orders table for order headers
- sales_order_items table for order line items (one-to-many relation)
- sales_deliver_infos table for delivery information (one-to-many relation)

#### Scenario: Create sales order in MySQL
- **WHEN** user creates a new sales order
- **THEN** system stores order header in sales_orders table and items in sales_order_items table

#### Scenario: Query sales order with items
- **WHEN** user queries a sales order by order_no
- **THEN** system returns order header with all related items using prefetch_related

### Requirement: Sales order number generation
The system SHALL generate unique sales order numbers with format SO{YYYYMMDD}{0001}.

#### Scenario: Generate order number
- **WHEN** creating a new sales order
- **THEN** system generates order_no like SO202605150001 based on date and sequence

### Requirement: Sales order CRUD operations
The system SHALL provide full CRUD operations for sales orders using Tortoise ORM.

#### Scenario: List sales orders with pagination
- **WHEN** user requests sales order list with page and page_size
- **THEN** system returns paginated results with total count

#### Scenario: Update sales order
- **WHEN** user updates a draft sales order
- **THEN** system updates order and related items in MySQL

#### Scenario: Delete sales order
- **WHEN** user deletes a draft or cancelled sales order
- **THEN** system deletes order and all related items (CASCADE)