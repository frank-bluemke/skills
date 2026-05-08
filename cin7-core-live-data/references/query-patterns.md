# Query Patterns

## Product Search

Use `find_products` when:

- the user gives a partial SKU
- the user gives a partial product name
- the request needs disambiguation before cost or sales lookup

## Product Cost

Use `get_product_cost` when:

- the user asks for cost
- the user asks for average unit cost
- the user asks for current selling price tiers and optionally supplier costs

Primary source:

- `/product`
- important fields: `SKU`, `Name`, `AverageCost`, `PriceTiers`, optional `Suppliers[].Cost`

## Sale Drill-Down

Use `list_sales` and `get_sale` when:

- the user wants recent sales
- the user wants one order inspected
- the user wants line items, invoices, fulfilments, or credit notes

Primary sources:

- `/saleList`
- `/sale`

## Inventory Availability

Use `get_product_availability` when:

- the user asks what inventory is available
- the user asks for on-hand, allocated, on-order, or in-transit numbers
- the user asks for stock at a specific location or batch

Primary source:

- `/ref/productavailability`

Important fields:

- `Location`
- `Batch`
- `OnHand`
- `Allocated`
- `Available`
- `OnOrder`
- `StockOnHand`
- `InTransit`
- `NextDeliveryDate`

## Units Sold

Use `get_units_sold` when:

- the user asks how many units were sold in a date range
- the user wants gross versus net quantity
- the user cares whether the result comes from order lines or invoice lines

Primary sources:

- `/saleList` for candidate Sale IDs and date metadata
- `/sale` for order, invoice, and credit-note lines

Always report:

- the date field used
- the line source used
- whether credit notes were subtracted
- whether the result was truncated because of scan limits

## Purchase Drill-Down

Use `list_purchases` and `get_purchase` when:

- the user wants recent purchase orders
- the user wants one purchase inspected
- the user wants purchase order, stock received, invoice, or credit note sections

Primary sources:

- `/purchaseList`
- `/purchase`

## Units Ordered

Use `get_units_ordered` when:

- the user asks how many units were ordered in a date range
- the user wants purchase-order quantities for a SKU or product name

Primary sources:

- `/purchaseList` for candidate purchase IDs and date metadata
- `/purchase` for `Order.Lines`

Always report:

- the date field used
- that the aggregation source is `Purchase.Order.Lines`
- that the current implementation is limited to simple purchases because `/purchase` is the documented simple-purchase detail endpoint
- whether the result was truncated because of scan limits
