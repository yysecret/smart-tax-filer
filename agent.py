import os
import json
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic import BaseModel
from pathlib import Path
from typing import Optional

# 1. Load the environment variables FIRST
load_dotenv() 

# 2. Check if the key actually loaded (optional debugging)
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found! Check your .env file.")

# 3. NOW initialize the model
# Using gpt-4o which supports vision/image analysis
model = OpenAIChatModel('gpt-4o')

# 4. Define the Pydantic model for receipt data
class ReceiptData(BaseModel):
    amount: float
    category: str
    merchant: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    audit_reasoning: Optional[str] = None

# 5. Create the agent with result type using generic syntax
agent = Agent[ReceiptData](
    model,
    system_prompt=(
        "You are a tax receipt analyzer. Extract key information from receipt images. "
        "Return the amount spent, categorize it (e.g., 'Business Meals', 'Office Supplies', "
        "'Travel', 'Equipment', 'Utilities', 'Software', etc.), merchant name, date, and description. "
        "Also provide audit_reasoning explaining your categorization decision for tax compliance purposes."
    )
)

# 6. Define the async function to process receipts
async def process_receipt(file_path: str) -> ReceiptData:
    """Process a receipt image and extract tax-relevant information."""
    image_path = Path(file_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Receipt file not found: {file_path}")
    
    # Read image file as bytes and use BinaryContent
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Use BinaryContent to pass image bytes directly
    from pydantic_ai.messages import BinaryContent
    
    # Detect media type from file extension
    # ImageMediaType is a Literal type with values: 'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    ext = image_path.suffix.lower()
    if ext in ['.jpg', '.jpeg']:
        media_type = 'image/jpeg'
    elif ext == '.png':
        media_type = 'image/png'
    elif ext == '.gif':
        media_type = 'image/gif'
    elif ext == '.webp':
        media_type = 'image/webp'
    else:
        media_type = 'image/jpeg'  # Default to JPEG
    
    # Create BinaryContent with image bytes
    image_content = BinaryContent(
        data=image_bytes,
        media_type=media_type
    )
    
    # Use agent.run with prompt text and BinaryContent
    result = await agent.run(
        [
            "Analyze this receipt image and extract the amount, category, merchant, date, and description. "
            "Provide audit_reasoning explaining why this expense fits into the selected category for tax deduction purposes.",
            image_content
        ]
    )
    
    # Access the result output
    # With Agent[ReceiptData], result.output should be a ReceiptData instance
    output = result.output
    
    # Handle different return types
    if isinstance(output, ReceiptData):
        return output
    elif isinstance(output, str):
        # If output is a string, try to parse it as JSON first
        try:
            # Try parsing as JSON first
            data_dict = json.loads(output)
            return ReceiptData(**data_dict)
        except json.JSONDecodeError:
            # If not valid JSON, try to extract structured data from markdown/text format
            import re
            
            # Extract amount - look for patterns like "$736.37" or "Amount: $736.37"
            amount_match = re.search(r'\$\s*([\d,]+\.?\d*)', output)
            amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0
            
            # Extract category - look for "Category: ..." or "**Category**: ..."
            category_match = re.search(r'(?:Category|category)[:\*\s]+([^\n\-]+)', output, re.IGNORECASE)
            category = category_match.group(1).strip().strip('*').strip() if category_match else "Unknown"
            
            # Extract merchant - look for "Merchant: ..." or "**Merchant**: ..."
            merchant_match = re.search(r'(?:Merchant|merchant)[:\*\s]+([^\n\-]+)', output, re.IGNORECASE)
            merchant = merchant_match.group(1).strip().strip('*').strip() if merchant_match else None
            
            # Extract date - look for "Date: ..." or "**Date**: ..."
            date_match = re.search(r'(?:Date|date)[:\*\s]+([^\n\-]+)', output, re.IGNORECASE)
            date = date_match.group(1).strip().strip('*').strip() if date_match else None
            
            # Extract description - look for "Description: ..." or everything after "Description:"
            desc_match = re.search(r'(?:Description|description)[:\*\s]+([^\n]+(?:\n[^-]+)*)', output, re.IGNORECASE | re.DOTALL)
            description = desc_match.group(1).strip().strip('*').strip() if desc_match else None
            
            # Extract audit reasoning - look for "Audit Reasoning", "Reasoning", "Justification", etc.
            reasoning_match = re.search(
                r'(?:Audit Reasoning|Reasoning|Justification|Rationale)[:\*\s]+([^\n]+(?:\n[^-]+)*)',
                output, re.IGNORECASE | re.DOTALL
            )
            audit_reasoning = reasoning_match.group(1).strip().strip('*').strip() if reasoning_match else None
            
            # If no explicit reasoning found, use the full agent response as reasoning
            if not audit_reasoning:
                audit_reasoning = output.strip()
            
            # Clean up the extracted values
            if category:
                category = re.sub(r'^\*\*|\*\*$', '', category).strip()
            if merchant:
                merchant = re.sub(r'^\*\*|\*\*$', '', merchant).strip()
            if date:
                date = re.sub(r'^\*\*|\*\*$', '', date).strip()
            if description:
                description = re.sub(r'^\*\*|\*\*$', '', description).strip()
                # Remove multiple newlines and clean up
                description = re.sub(r'\n+', ' ', description).strip()
            if audit_reasoning:
                audit_reasoning = re.sub(r'^\*\*|\*\*$', '', audit_reasoning).strip()
                # Keep newlines but clean up excessive whitespace
                audit_reasoning = re.sub(r'\n{3,}', '\n\n', audit_reasoning).strip()
            
            # Create ReceiptData from extracted values
            try:
                return ReceiptData(
                    amount=amount,
                    category=category,
                    merchant=merchant,
                    date=date,
                    description=description,
                    audit_reasoning=audit_reasoning
                )
            except Exception as e:
                # If we can't create ReceiptData, raise error with parsed values for debugging
                raise ValueError(
                    f"Failed to create ReceiptData from parsed text. "
                    f"Amount: {amount}, Category: {category}, Merchant: {merchant}, Date: {date}, "
                    f"Description: {description[:100]}. Error: {e}. Original response: {output[:500]}"
                )
    elif isinstance(output, dict):
        # If output is a dict, convert it to ReceiptData
        return ReceiptData(**output)
    else:
        raise TypeError(
            f"Unexpected result type from agent: {type(output)}. "
            f"Expected ReceiptData, str, or dict. Got: {repr(output)[:200]}"
        )