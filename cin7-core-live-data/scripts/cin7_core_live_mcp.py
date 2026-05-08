#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time as datetime_time, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP


DEFAULT_BASE_URL = "https://inventory.dearsystems.com/ExternalApi/v2"
DEFAULT_RATE_LIMIT_PER_MINUTE = 55
DEFAULT_SEARCH_LIMIT = 25
MAX_PAGE_SIZE = 100
MAX_RETRIES = 4


class Cin7Error(RuntimeError):
    """Raised when the Cin7 API request cannot be completed safely."""


@dataclass(frozen=True)
class Cin7Config:
    account_id: str
    application_key: str
    base_url: str = DEFAULT_BASE_URL
    rate_limit_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE


class RateLimiter:
    """Simple pacing guard to stay below the Cin7 per-minute cap."""

    def __init__(self, requests_per_minute: int) -> None:
        safe_rate = max(1, requests_per_minute)
        self._min_interval = 60.0 / safe_rate
        self._lock = threading.Lock()
        self._next_time = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._next_time:
                time.sleep(self._next_time - now)
                now = time.monotonic()
            self._next_time = now + self._min_interval


def _load_config() -> Cin7Config:
    account_id = os.environ.get("CIN7_ACCOUNT_ID", "").strip()
    application_key = os.environ.get("CIN7_APPLICATION_KEY", "").strip()
    if not account_id or not application_key:
        raise Cin7Error(
            "Missing Cin7 credentials. Set CIN7_ACCOUNT_ID and CIN7_APPLICATION_KEY."
        )

    base_url = os.environ.get("CIN7_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    rate_limit_per_minute = int(
        os.environ.get(
            "CIN7_RATE_LIMIT_PER_MINUTE",
            str(DEFAULT_RATE_LIMIT_PER_MINUTE),
        )
    )
    return Cin7Config(
        account_id=account_id,
        application_key=application_key,
        base_url=base_url,
        rate_limit_per_minute=rate_limit_per_minute,
    )


def _parse_iso_datetime(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not value:
        return None

    text = value.strip()
    if not text:
        return None

    if "T" not in text:
        parsed = datetime.fromisoformat(text)
        parsed = datetime.combine(
            parsed.date(),
            datetime_time.max if end_of_day else datetime_time.min,
            tzinfo=timezone.utc,
        )
        return parsed

    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_iso_datetime(value: str | None, *, end_of_day: bool = False) -> str | None:
    parsed = _parse_iso_datetime(value, end_of_day=end_of_day)
    if parsed is None:
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def _safe_json_loads(text: str, *, fallback: Any) -> Any:
    if not text.strip():
        return fallback
    return json.loads(text)


def _product_summary(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": product.get("ID"),
        "sku": product.get("SKU"),
        "name": product.get("Name"),
        "status": product.get("Status"),
        "type": product.get("Type"),
        "average_cost": product.get("AverageCost"),
        "price_tiers": product.get("PriceTiers") or {
            f"PriceTier{i}": product.get(f"PriceTier{i}") for i in range(1, 11)
        },
    }


class Cin7Client:
    def __init__(self, config: Cin7Config) -> None:
        self._config = config
        self._rate_limiter = RateLimiter(config.rate_limit_per_minute)

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized_path = path if path.startswith("/") else f"/{path}"
        query_params = {
            key: value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        query = urllib.parse.urlencode(query_params, doseq=True)
        url = f"{self._config.base_url}{normalized_path}"
        if query:
            url = f"{url}?{query}"

        headers = {
            "api-auth-accountid": self._config.account_id,
            "api-auth-applicationkey": self._config.application_key,
            "Content-Type": "application/json",
        }

        for attempt in range(MAX_RETRIES + 1):
            self._rate_limiter.wait()
            request = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    body = response.read().decode("utf-8")
                    if not body:
                        return {}
                    return json.loads(body)
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code in {429, 500} and attempt < MAX_RETRIES:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise Cin7Error(
                    f"Cin7 API GET {normalized_path} failed with {exc.code}: {body}"
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < MAX_RETRIES:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise Cin7Error(f"Cin7 API GET {normalized_path} failed: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise Cin7Error(f"Cin7 API returned invalid JSON for {normalized_path}.") from exc

        raise Cin7Error(f"Cin7 API GET {normalized_path} exhausted retries.")

    def find_products(
        self,
        *,
        query: str,
        include_deprecated: bool = False,
        include_suppliers: bool = False,
        limit: int = DEFAULT_SEARCH_LIMIT,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        merged: dict[str, dict[str, Any]] = {}

        if query:
            for params in (
                {"Sku": query},
                {"Name": query},
            ):
                payload = self.get(
                    "/product",
                    params={
                        "Page": 1,
                        "Limit": limit,
                        "IncludeDeprecated": str(include_deprecated).lower(),
                        "IncludeSuppliers": str(include_suppliers).lower(),
                        **params,
                    },
                )
                for product in payload.get("Products", []):
                    product_id = product.get("ID") or product.get("SKU") or product.get("Name")
                    merged[str(product_id)] = product

        products = list(merged.values())
        products.sort(key=lambda product: (product.get("SKU") or "", product.get("Name") or ""))
        return products[:limit]

    def list_sales(
        self,
        *,
        page: int = 1,
        limit: int = DEFAULT_SEARCH_LIMIT,
        search: str | None = None,
        created_since: str | None = None,
        updated_since: str | None = None,
        updated_until: str | None = None,
        order_status: str | None = None,
        status: str | None = None,
        combined_invoice_status: str | None = None,
    ) -> dict[str, Any]:
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        return self.get(
            "/saleList",
            params={
                "Page": page,
                "Limit": limit,
                "Search": search,
                "CreatedSince": created_since,
                "UpdatedSince": updated_since,
                "UpdatedUntil": updated_until,
                "OrderStatus": order_status,
                "Status": status,
                "CombinedInvoiceStatus": combined_invoice_status,
            },
        )

    def list_purchases(
        self,
        *,
        page: int = 1,
        limit: int = DEFAULT_SEARCH_LIMIT,
        search: str | None = None,
        required_by: str | None = None,
        updated_since: str | None = None,
        updated_until: str | None = None,
        order_status: str | None = None,
        restock_received_status: str | None = None,
        invoice_status: str | None = None,
        credit_note_status: str | None = None,
        unstock_status: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        return self.get(
            "/purchaseList",
            params={
                "Page": page,
                "Limit": limit,
                "Search": search,
                "RequiredBy": required_by,
                "UpdatedSince": updated_since,
                "UpdatedUntil": updated_until,
                "OrderStatus": order_status,
                "RestockReceivedStatus": restock_received_status,
                "InvoiceStatus": invoice_status,
                "CreditNoteStatus": credit_note_status,
                "UnstockStatus": unstock_status,
                "Status": status,
            },
        )

    def get_product_availability(
        self,
        *,
        page: int = 1,
        limit: int = DEFAULT_SEARCH_LIMIT,
        product_id: str | None = None,
        name: str | None = None,
        sku: str | None = None,
        location: str | None = None,
        batch: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        return self.get(
            "/ref/productavailability",
            params={
                "Page": page,
                "Limit": limit,
                "ID": product_id,
                "Name": name,
                "Sku": sku,
                "Location": location,
                "Batch": batch,
                "Category": category,
            },
        )

    def get_purchase(self, purchase_id: str) -> dict[str, Any]:
        return self.get("/purchase", params={"ID": purchase_id})

    def get_sale(self, sale_id: str, *, include_transactions: bool = False) -> dict[str, Any]:
        return self.get(
            "/sale",
            params={
                "ID": sale_id,
                "IncludeTransactions": str(include_transactions).lower(),
            },
        )


_CLIENT: Cin7Client | None = None
_CLIENT_LOCK = threading.Lock()


def _client() -> Cin7Client:
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                _CLIENT = Cin7Client(_load_config())
    return _CLIENT


def _line_matches(
    line: dict[str, Any],
    *,
    candidate_ids: set[str],
    candidate_skus: set[str],
    query: str,
) -> bool:
    product_id = str(line.get("ProductID") or "").strip()
    sku = str(line.get("SKU") or "").strip().lower()
    name = str(line.get("Name") or line.get("ProductName") or "").strip().lower()
    normalized_query = query.strip().lower()

    if product_id and product_id in candidate_ids:
        return True
    if sku and sku in candidate_skus:
        return True
    if normalized_query and (normalized_query in sku or normalized_query in name):
        return True
    return False


def _extract_sale_lines(sale: dict[str, Any], line_source: str) -> list[dict[str, Any]]:
    if line_source == "quote":
        return list((sale.get("Quote") or {}).get("Lines") or [])
    if line_source == "order":
        return list((sale.get("Order") or {}).get("Lines") or [])
    if line_source == "invoice":
        lines: list[dict[str, Any]] = []
        for invoice in sale.get("Invoices") or []:
            lines.extend(invoice.get("Lines") or [])
        return lines
    if line_source == "credit_note":
        lines = []
        for credit_note in sale.get("CreditNotes") or []:
            lines.extend(credit_note.get("Lines") or [])
        return lines
    raise Cin7Error(f"Unsupported line source: {line_source}")


def _extract_purchase_lines(purchase: dict[str, Any], line_source: str) -> list[dict[str, Any]]:
    if line_source == "order":
        return list((purchase.get("Order") or {}).get("Lines") or [])
    if line_source == "stock_received":
        return list((purchase.get("StockReceived") or {}).get("Lines") or [])
    if line_source == "invoice":
        return list((purchase.get("Invoice") or {}).get("Lines") or [])
    if line_source == "credit_note":
        return list((purchase.get("CreditNote") or {}).get("Lines") or [])
    raise Cin7Error(f"Unsupported purchase line source: {line_source}")


def _sale_matches_date_window(
    sale_row: dict[str, Any],
    *,
    start: datetime | None,
    end: datetime | None,
    date_field: str,
) -> bool:
    if date_field == "order":
        raw_value = sale_row.get("OrderDate")
    elif date_field == "invoice":
        raw_value = sale_row.get("InvoiceDate")
    elif date_field == "updated":
        raw_value = sale_row.get("Updated")
    else:
        raise Cin7Error(f"Unsupported date field: {date_field}")

    if not raw_value:
        return False

    parsed = _parse_iso_datetime(str(raw_value))
    if parsed is None:
        return False
    if start and parsed < start:
        return False
    if end and parsed > end:
        return False
    return True


def _purchase_matches_date_window(
    purchase_row: dict[str, Any],
    *,
    start: datetime | None,
    end: datetime | None,
    date_field: str,
) -> bool:
    if date_field == "order":
        raw_value = purchase_row.get("OrderDate")
    elif date_field == "invoice":
        raw_value = purchase_row.get("InvoiceDate")
    elif date_field == "updated":
        raw_value = purchase_row.get("LastUpdatedDate")
    elif date_field == "required_by":
        raw_value = purchase_row.get("RequiredBy")
    else:
        raise Cin7Error(f"Unsupported purchase date field: {date_field}")

    if not raw_value:
        return False

    parsed = _parse_iso_datetime(str(raw_value))
    if parsed is None:
        return False
    if start and parsed < start:
        return False
    if end and parsed > end:
        return False
    return True


mcp = FastMCP("cin7-core-live", json_response=True)


@mcp.tool()
def find_products(
    query: str,
    include_deprecated: bool = False,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> dict[str, Any]:
    """Search Cin7 products by partial SKU or product name."""

    products = _client().find_products(
        query=query,
        include_deprecated=include_deprecated,
        limit=limit,
    )
    return {
        "query": query,
        "count": len(products),
        "products": [_product_summary(product) for product in products],
    }


@mcp.tool()
def get_product_cost(
    product_query: str,
    include_supplier_costs: bool = False,
) -> dict[str, Any]:
    """Return AverageCost and pricing info for the best matching product."""

    products = _client().find_products(
        query=product_query,
        include_suppliers=include_supplier_costs,
        limit=10,
    )
    if not products:
        return {
            "query": product_query,
            "matched": False,
            "message": "No matching product was found.",
        }

    exact_match = None
    normalized_query = product_query.strip().lower()
    for product in products:
        if (product.get("SKU") or "").lower() == normalized_query:
            exact_match = product
            break
    chosen = exact_match or products[0]

    response = {
        "query": product_query,
        "matched": True,
        "ambiguous": len(products) > 1 and exact_match is None,
        "selected_product": _product_summary(chosen),
        "candidates": [_product_summary(product) for product in products[:5]],
        "cost_basis": "Product.AverageCost",
    }
    if include_supplier_costs:
        response["supplier_costs"] = [
            {
                "supplier_id": supplier.get("SupplierID"),
                "supplier_name": supplier.get("SupplierName"),
                "supplier_inventory_code": supplier.get("SupplierInventoryCode"),
                "cost": supplier.get("Cost"),
                "fixed_cost": supplier.get("FixedCost"),
                "currency": supplier.get("Currency"),
            }
            for supplier in chosen.get("Suppliers") or []
        ]
    return response


@mcp.tool()
def get_product_availability(
    product_query: str = "",
    sku: str = "",
    location: str = "",
    batch: str = "",
    category: str = "",
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> dict[str, Any]:
    """Return inventory availability rows from /ref/productavailability."""

    client = _client()
    resolved_products: list[dict[str, Any]] = []
    availability_rows: list[dict[str, Any]] = []

    if sku:
        payload = client.get_product_availability(
            sku=sku,
            location=location or None,
            batch=batch or None,
            category=category or None,
            limit=limit,
        )
        return {
            "query": product_query or sku,
            "filters": {
                "sku": sku,
                "location": location or None,
                "batch": batch or None,
                "category": category or None,
            },
            "total": payload.get("Total"),
            "page": payload.get("Page"),
            "rows": payload.get("ProductAvailabilityList", []),
        }

    if product_query:
        resolved_products = client.find_products(query=product_query, limit=5)
        for product in resolved_products:
            product_payload = client.get_product_availability(
                product_id=product.get("ID"),
                location=location or None,
                batch=batch or None,
                category=category or None,
                limit=limit,
            )
            availability_rows.extend(product_payload.get("ProductAvailabilityList", []))
            if len(availability_rows) >= limit:
                break

    if not product_query:
        payload = client.get_product_availability(
            location=location or None,
            batch=batch or None,
            category=category or None,
            limit=limit,
        )
        availability_rows = payload.get("ProductAvailabilityList", [])
        total = payload.get("Total")
        page = payload.get("Page")
    else:
        total = len(availability_rows)
        page = 1

    return {
        "query": product_query or None,
        "resolved_products": [_product_summary(product) for product in resolved_products],
        "filters": {
            "location": location or None,
            "batch": batch or None,
            "category": category or None,
        },
        "total": total,
        "page": page,
        "rows": availability_rows[:limit],
    }


@mcp.tool()
def list_sales(
    search: str = "",
    created_since: str = "",
    updated_since: str = "",
    updated_until: str = "",
    order_status: str = "",
    status: str = "",
    combined_invoice_status: str = "",
    limit: int = DEFAULT_SEARCH_LIMIT,
    page: int = 1,
) -> dict[str, Any]:
    """Return sale list rows from /saleList using Cin7's list filters."""

    payload = _client().list_sales(
        page=page,
        limit=limit,
        search=search or None,
        created_since=_format_iso_datetime(created_since) if created_since else None,
        updated_since=_format_iso_datetime(updated_since) if updated_since else None,
        updated_until=_format_iso_datetime(updated_until, end_of_day=True)
        if updated_until
        else None,
        order_status=order_status or None,
        status=status or None,
        combined_invoice_status=combined_invoice_status or None,
    )
    return {
        "page": payload.get("Page"),
        "total": payload.get("Total"),
        "sales": payload.get("SaleList", []),
    }


@mcp.tool()
def list_purchases(
    search: str = "",
    required_by: str = "",
    updated_since: str = "",
    updated_until: str = "",
    order_status: str = "",
    restock_received_status: str = "",
    invoice_status: str = "",
    credit_note_status: str = "",
    unstock_status: str = "",
    status: str = "",
    limit: int = DEFAULT_SEARCH_LIMIT,
    page: int = 1,
) -> dict[str, Any]:
    """Return purchase list rows from /purchaseList using Cin7's list filters."""

    payload = _client().list_purchases(
        page=page,
        limit=limit,
        search=search or None,
        required_by=_format_iso_datetime(required_by, end_of_day=True)
        if required_by
        else None,
        updated_since=_format_iso_datetime(updated_since) if updated_since else None,
        updated_until=_format_iso_datetime(updated_until, end_of_day=True)
        if updated_until
        else None,
        order_status=order_status or None,
        restock_received_status=restock_received_status or None,
        invoice_status=invoice_status or None,
        credit_note_status=credit_note_status or None,
        unstock_status=unstock_status or None,
        status=status or None,
    )
    return {
        "page": payload.get("Page"),
        "total": payload.get("Total"),
        "purchases": payload.get("PurchaseList", []),
    }


@mcp.tool()
def get_purchase(purchase_id: str) -> dict[str, Any]:
    """Return the full /purchase payload for a specific purchase ID."""

    return _client().get_purchase(purchase_id)


@mcp.tool()
def get_sale(
    sale_id: str,
    include_transactions: bool = False,
) -> dict[str, Any]:
    """Return the full /sale payload for a specific SaleID."""

    return _client().get_sale(sale_id, include_transactions=include_transactions)


@mcp.tool()
def get_units_sold(
    product_query: str,
    from_date: str,
    to_date: str,
    date_field: str = "order",
    line_source: str = "order",
    quantity_mode: str = "gross",
    max_sales: int = DEFAULT_SEARCH_LIMIT,
    search_page_limit: int = 5,
    order_status: str = "",
    status: str = "",
) -> dict[str, Any]:
    """Aggregate quantity sold for matching products over a date range."""

    if quantity_mode not in {"gross", "net"}:
        raise Cin7Error("quantity_mode must be 'gross' or 'net'.")
    if date_field not in {"order", "invoice", "updated"}:
        raise Cin7Error("date_field must be 'order', 'invoice', or 'updated'.")
    if line_source not in {"quote", "order", "invoice", "credit_note"}:
        raise Cin7Error("line_source must be quote, order, invoice, or credit_note.")

    start = _parse_iso_datetime(from_date)
    end = _parse_iso_datetime(to_date, end_of_day=True)
    if start is None or end is None:
        raise Cin7Error("from_date and to_date are required and must be ISO-like dates.")
    if end < start:
        raise Cin7Error("to_date must be on or after from_date.")

    client = _client()
    products = client.find_products(query=product_query, limit=10)
    candidate_ids = {str(product.get("ID")) for product in products if product.get("ID")}
    candidate_skus = {
        str(product.get("SKU")).strip().lower()
        for product in products
        if product.get("SKU")
    }

    candidate_sales: list[dict[str, Any]] = []
    total_available = None
    for page in range(1, search_page_limit + 1):
        if len(candidate_sales) >= max_sales:
            break
        payload = client.list_sales(
            page=page,
            limit=min(MAX_PAGE_SIZE, max_sales),
            created_since=_format_iso_datetime(from_date) if date_field == "order" else None,
            updated_since=_format_iso_datetime(from_date) if date_field != "order" else None,
            updated_until=_format_iso_datetime(to_date, end_of_day=True)
            if date_field == "updated"
            else None,
            order_status=order_status or None,
            status=status or None,
        )
        total_available = payload.get("Total")
        for sale_row in payload.get("SaleList", []):
            if not _sale_matches_date_window(
                sale_row,
                start=start,
                end=end,
                date_field=date_field,
            ):
                continue
            candidate_sales.append(sale_row)
            if len(candidate_sales) >= max_sales:
                break

        page_size = len(payload.get("SaleList", []))
        if page_size == 0:
            break

    gross_quantity = 0.0
    credited_quantity = 0.0
    matched_sales: list[dict[str, Any]] = []
    for sale_row in candidate_sales:
        sale_detail = client.get_sale(sale_row["SaleID"])
        matched_line_quantity = 0.0
        for line in _extract_sale_lines(sale_detail, line_source):
            if _line_matches(
                line,
                candidate_ids=candidate_ids,
                candidate_skus=candidate_skus,
                query=product_query,
            ):
                matched_line_quantity += float(line.get("Quantity") or 0)

        matched_credit_quantity = 0.0
        if quantity_mode == "net":
            for line in _extract_sale_lines(sale_detail, "credit_note"):
                if _line_matches(
                    line,
                    candidate_ids=candidate_ids,
                    candidate_skus=candidate_skus,
                    query=product_query,
                ):
                    matched_credit_quantity += float(line.get("Quantity") or 0)

        if matched_line_quantity or matched_credit_quantity:
            gross_quantity += matched_line_quantity
            credited_quantity += matched_credit_quantity
            matched_sales.append(
                {
                    "sale_id": sale_row.get("SaleID"),
                    "order_number": sale_row.get("OrderNumber"),
                    "order_date": sale_row.get("OrderDate"),
                    "invoice_date": sale_row.get("InvoiceDate"),
                    "status": sale_row.get("Status"),
                    "line_quantity": matched_line_quantity,
                    "credited_quantity": matched_credit_quantity,
                }
            )

    net_quantity = gross_quantity - credited_quantity
    truncated = False
    if total_available is not None and isinstance(total_available, int):
        truncated = total_available > len(candidate_sales) or len(candidate_sales) >= max_sales

    return {
        "query": product_query,
        "matched_products": [_product_summary(product) for product in products[:5]],
        "date_field": date_field,
        "line_source": line_source,
        "quantity_mode": quantity_mode,
        "from_date": _format_iso_datetime(from_date),
        "to_date": _format_iso_datetime(to_date, end_of_day=True),
        "gross_quantity": gross_quantity,
        "credited_quantity": credited_quantity,
        "net_quantity": net_quantity,
        "matched_sales_count": len(matched_sales),
        "scanned_sales_count": len(candidate_sales),
        "matched_sales": matched_sales[:20],
        "truncated": truncated,
        "truncation_reason": (
            "Result set may be partial because max_sales/search_page_limit was reached."
            if truncated
            else None
        ),
    }


@mcp.tool()
def get_units_ordered(
    product_query: str,
    from_date: str,
    to_date: str,
    date_field: str = "order",
    line_source: str = "order",
    max_purchases: int = DEFAULT_SEARCH_LIMIT,
    search_page_limit: int = 5,
    order_status: str = "",
    status: str = "",
) -> dict[str, Any]:
    """Aggregate ordered quantity for matching products over a date range."""

    if date_field not in {"order", "invoice", "updated", "required_by"}:
        raise Cin7Error(
            "date_field must be 'order', 'invoice', 'updated', or 'required_by'."
        )
    if line_source not in {"order", "stock_received", "invoice", "credit_note"}:
        raise Cin7Error(
            "line_source must be order, stock_received, invoice, or credit_note."
        )

    start = _parse_iso_datetime(from_date)
    end = _parse_iso_datetime(to_date, end_of_day=True)
    if start is None or end is None:
        raise Cin7Error("from_date and to_date are required and must be ISO-like dates.")
    if end < start:
        raise Cin7Error("to_date must be on or after from_date.")

    client = _client()
    products = client.find_products(query=product_query, limit=10)
    candidate_ids = {str(product.get("ID")) for product in products if product.get("ID")}
    candidate_skus = {
        str(product.get("SKU")).strip().lower()
        for product in products
        if product.get("SKU")
    }

    candidate_purchases: list[dict[str, Any]] = []
    total_available = None
    for page in range(1, search_page_limit + 1):
        if len(candidate_purchases) >= max_purchases:
            break
        payload = client.list_purchases(
            page=page,
            limit=min(MAX_PAGE_SIZE, max_purchases),
            required_by=_format_iso_datetime(to_date, end_of_day=True)
            if date_field == "required_by"
            else None,
            updated_since=_format_iso_datetime(from_date) if date_field == "updated" else None,
            updated_until=_format_iso_datetime(to_date, end_of_day=True)
            if date_field == "updated"
            else None,
            order_status=order_status or None,
            status=status or None,
        )
        total_available = payload.get("Total")
        for purchase_row in payload.get("PurchaseList", []):
            if not _purchase_matches_date_window(
                purchase_row,
                start=start,
                end=end,
                date_field=date_field,
            ):
                continue
            candidate_purchases.append(purchase_row)
            if len(candidate_purchases) >= max_purchases:
                break

        page_size = len(payload.get("PurchaseList", []))
        if page_size == 0:
            break

    ordered_quantity = 0.0
    matched_purchases: list[dict[str, Any]] = []
    for purchase_row in candidate_purchases:
        purchase_detail = client.get_purchase(purchase_row["ID"])
        matched_line_quantity = 0.0
        for line in _extract_purchase_lines(purchase_detail, line_source):
            if _line_matches(
                line,
                candidate_ids=candidate_ids,
                candidate_skus=candidate_skus,
                query=product_query,
            ):
                matched_line_quantity += float(line.get("Quantity") or 0)

        if matched_line_quantity:
            ordered_quantity += matched_line_quantity
            matched_purchases.append(
                {
                    "purchase_id": purchase_row.get("ID"),
                    "order_number": purchase_row.get("OrderNumber"),
                    "supplier": purchase_row.get("Supplier"),
                    "order_date": purchase_row.get("OrderDate"),
                    "invoice_date": purchase_row.get("InvoiceDate"),
                    "required_by": purchase_row.get("RequiredBy"),
                    "status": purchase_row.get("Status"),
                    "line_quantity": matched_line_quantity,
                }
            )

    truncated = False
    if total_available is not None and isinstance(total_available, int):
        truncated = total_available > len(candidate_purchases) or len(candidate_purchases) >= max_purchases

    return {
        "query": product_query,
        "matched_products": [_product_summary(product) for product in products[:5]],
        "date_field": date_field,
        "line_source": line_source,
        "source_basis": "Purchase.Order.Lines from /purchase",
        "simple_purchase_only": True,
        "from_date": _format_iso_datetime(from_date),
        "to_date": _format_iso_datetime(to_date, end_of_day=True),
        "ordered_quantity": ordered_quantity,
        "matched_purchases_count": len(matched_purchases),
        "scanned_purchases_count": len(candidate_purchases),
        "matched_purchases": matched_purchases[:20],
        "truncated": truncated,
        "truncation_reason": (
            "Result set may be partial because max_purchases/search_page_limit was reached."
            if truncated
            else None
        ),
        "limitation": (
            "Current ordered-units aggregation uses /purchase, which the Cin7 blueprint documents as the simple-purchase detail endpoint."
        ),
    }


@mcp.tool()
def raw_get(
    path: str,
    params_json: str = "{}",
) -> dict[str, Any]:
    """Perform a read-only GET against a Cin7 Core endpoint path."""

    params = _safe_json_loads(params_json, fallback={})
    if not isinstance(params, dict):
        raise Cin7Error("params_json must decode to a JSON object.")
    return _client().get(path, params=params)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Cin7 Core MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "http"),
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="MCP transport to use.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Host for HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port for HTTP transport.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    last_error: Exception | None = None
    transports = (
        ("streamable-http", "/mcp"),
        ("http", "/mcp"),
        ("streamable-http", None),
        ("http", None),
    )
    if args.transport == "http":
        transports = (
            ("http", "/mcp"),
            ("http", None),
            ("streamable-http", "/mcp"),
            ("streamable-http", None),
        )

    for transport_name, path in transports:
        try:
            kwargs: dict[str, Any] = {
                "transport": transport_name,
                "host": args.host,
                "port": args.port,
            }
            if path is not None:
                kwargs["path"] = path
            mcp.run(**kwargs)
            return
        except TypeError as exc:
            last_error = exc
            continue
        except ValueError as exc:
            last_error = exc
            continue

    raise Cin7Error(
        "Unable to start HTTP MCP transport with the installed mcp package. "
        "Try a newer SDK or run in stdio mode."
    ) from last_error


if __name__ == "__main__":
    main()
