# Cin7 Core API Endpoint Index

Use this file to find the right part of the blueprint quickly. After choosing a family, open the canonical section in `cin7-core-api.apib`.

## Reference And Setup

- Attribute Set: `/ref/attributeset`
- Bank Accounts: `/ref/account/bank`
- Brand: `/ref/brand`
- Carrier: `/ref/carrier`
- Chart of Accounts: `/ref/account`
- Location: `/ref/location`
- Payment Term: `/ref/paymentterm`
- Price Tiers: `/ref/priceTier`
- Tax: `/ref/tax`
- Templates: `/ref/templates`
- Unit of Measure: `/ref/unit`
- Me: `/me`, `/me/addresses`, `/me/contacts`

## Customers And Suppliers

- Customer: `/customer`
- Customer Default Template: `/ref/customer/templates`
- Customer Credits: `/ref/customer/credits`
- Supplier: `/supplier`
- Supplier Deposits: `/ref/supplier/deposits`

Use these families for account master data, contact records, addresses, and customer or supplier-specific reference information.

## Products And Catalog

- Product: `/product`
- Product Attachments: `/product/attachments`
- Product Availability: `/ref/productavailability`
- Product Category: `/ref/category`
- Product Family: `/productFamily`
- Product Family Attachments: `/productFamily/attachments`
- Markup Prices: `/ref/markupprices`
- Custom Prices: `/custom-prices`
- Product Discounts: `/reference/discount`
- Product Suppliers: `/product-suppliers`

Use these families for SKU master data, catalog hierarchy, supplier assignments, pricing, availability, BOM-related product flags, and catalog attachments.

## Production

- Factory Calendar: `/production/factoryCalendar`
- Product Production BOM: `/production/productionBOM`
- Product Family Production BOM: `/production/productionBOM/`
- Production Order: `/production/order`
- Production Order List: `/production/orderList`
- Production Run: `/production/order/run`
- Resource List: `/production/resourceList`
- Resource: `/production/resource`
- Suspend Reason: `/production/suspendReason`
- Work Centers: `/production/workcenters`

Use these families for manufacturing setup, BOM definitions, production scheduling, runs, and work-center or resource data.

## Purchases

- Purchase List: `/purchaseList`
- Purchase Credit Note List: `/purchaseCreditNoteList`
- Purchase: `/purchase`
- Purchase Order: `/purchase/order`
- Purchase Stock Received: `/purchase/stock`
- Purchase Invoice: `/purchase/invoice`
- Purchase Credit Note: `/purchase/creditnote`
- Purchase Payments: `/purchase/payment`
- Purchase Manual Journals: `/purchase/manualJournal`
- Purchase Attachments: `/purchase/attachment`
- Advanced Purchase: `/advanced-purchase`
- Advanced Purchase Stock Received: `/advanced-purchase/stock`
- Advanced Purchase Put Away: `/advanced-purchase/put-away`
- Advanced Purchase Invoice: `/advanced-purchase/invoice`
- Advanced Purchase Credit Note: `/advanced-purchase/creditnote`
- Advanced Purchase Payments: `/advanced-purchase/payment`
- Advanced Purchase Manual Journals: `/advanced-purchase/manualJournal`

Use purchase list endpoints for search and incremental sync. Use the task subresources when the workflow requires a specific purchase stage.

## Sales

- Sale List: `/saleList`
- Sale Credit Note List: `/saleCreditNoteList`
- Sale: `/sale`
- Sale Quote: `/sale/quote`
- Sale Order: `/sale/order`
- Sale Fulfilment: `/sale/fulfilment`
- Sale Fulfilment Pick: `/sale/fulfilment/pick`
- Sale Fulfilment Pack: `/sale/fulfilment/pack`
- Sale Fulfilment Ship: `/sale/fulfilment/ship`
- Sale Invoice: `/sale/invoice`
- Sale Credit Note: `/sale/creditnote`
- Sale Payments: `/sale/payment`
- Sale Manual Journals: `/sale/manualJournal`
- Sale Attachments: `/sale/attachment`

Use these families for quote-to-cash lifecycle work. Expect many operations to key off `TaskID`.

## Stock And Inventory Tasks

- Inventory Write-Off List: `/inventoryWriteOffList`
- Inventory Write-Off: `/inventoryWriteOff`
- Stock Adjustment List: `/stockadjustmentList`
- Stock Adjustment: `/stockadjustment`
- Stock Take List: `/stockTakeList`
- Stock Take: `/stocktake`
- Stock Transfer List: `/stockTransferList`
- Stock Transfer: `/stockTransfer`
- Stock Transfer Order: `/stockTransfer/order`
- Disassembly List: `/disassemblyList`
- Disassembly: `/disassembly`
- Disassembly Order: `/disassembly/order`
- Finished Goods List: `/finishedGoodsList`
- Finished Goods: `/finishedGoods`
- Finished Goods Order: `/finishedGoods/order`
- Finished Goods Pick: `/finishedGoods/pick`

Use these families for operational inventory changes and production-adjacent inventory workflows.

## Finance And Transactions

- Journal: `/journal`
- Money Task List: `/moneyTaskList`
- Money Operation: `/moneyOperation`
- Bank Transfer: `/bankTransfer`
- Transactions: `/transactions`

Use these families for accounting flows, cash movement, and transaction exports.

## Shipping And Reference Books

- Deals: `/reference/deals`
- Ship Zones: `/reference/shipZones`
- Ship Zones Enabled: `/reference/shipZonesEnabled`

Use these when sale or logistics work requires shipping configuration or pricing reference data.

## Webhooks

- Webhooks: `/webhooks`

Use this family for registering, updating, listing, or deleting outbound webhook subscriptions and for reviewing supported event types and payload examples.

## CRM

- Lead: `/crm/lead`
- Opportunity: `/crm/opportunity`
- Task: `/crm/task`
- Task Category: `/crm/taskcategory`
- Workflow: `/crm/workflow`
- Start a Workflow: `/crm/workflowstart`

Use these families for CRM object synchronization and workflow automation.

## Search Hints

- Search by path fragment when you know the endpoint: `rg -n "/sale/invoice|/purchase/stock|/product" references/cin7-core-api.apib`
- Search by model or field name when you know the payload concept: `rg -n "Available fields for Sale|AdditionalAttributes|TaskID" references/cin7-core-api.apib`
- Search by group when the feature area is only loosely known: `rg -n "^# Group Sale|^# Group Purchase|^# Group Product" references/cin7-core-api.apib`
