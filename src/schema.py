from pydantic import BaseModel, Field
from typing import Optional

class SharePurchaseAgreement(BaseModel):
    document_type: Optional[str] = Field(
        default=None, description="The type of the agreement Document (e.g., Share Purchase Agreement)"
    )
    effective_date: Optional[str] = Field(
        default=None, description="The effective date or closing date of the agreement"
    )
    buyer: Optional[str] = Field(
        default=None, description="Name of the buyer entity or individual"
    )
    company_target: Optional[str] = Field(
        default=None, description="Name of the target company being acquired"
    )
    seller: Optional[str] = Field(
        default=None, description="Name of the seller entity or individual"
    )
    shares_transacted: Optional[str] = Field(
        default=None, description="Number of shares or percentage of equity transacted"
    )
    cash_purchase_price: Optional[str] = Field(
        default=None, description="The cash purchase price or consideration amount"
    )
    escrow_agent: Optional[str] = Field(
        default=None, description="Name of the escrow agent, if any"
    )
    escrow_amount: Optional[str] = Field(
        default=None, description="The amount of funds held in escrow"
    )
    target_working_capital: Optional[str] = Field(
        default=None, description="The designated target working capital amount"
    )
    indemnification_de_minimis: Optional[str] = Field(
        default=None, description="The indemnification de minimis amount or per-claim threshold. Often called 'De Minimis Amount'. If not specified, look for minimum claim amounts in the Indemnification section."
    )
    indemnification_basket: Optional[str] = Field(
        default=None, description="The indemnification basket or deductible amount (aggregate threshold). Often called 'Basket'. Found in the Indemnification section (Article VII/Section 7)."
    )
    indemnification_cap: Optional[str] = Field(
        default=None, description="The indemnification cap or maximum liability limit. Often called 'Cap'. Found in the Indemnification section (Article VII/Section 7)."
    )
    governing_law: Optional[str] = Field(
        default=None, description="The state or jurisdiction whose laws govern the agreement (e.g., 'Delaware', 'New York'). Usually found in 'Governing Law' or 'Miscellaneous' sections."
    )
