# AI Commerce Layer

## Runtime Flow

```text
WhatsApp webhook
  -> parse_whatsapp_payload()
  -> WhatsAppWebhookService.process_payload()
  -> CommerceAIService.handle_incoming_message()
  -> PreprocessingService.preprocess_user_message()
  -> LLMService.extract_user_intent()
  -> ProductSearchService.search_products()
  -> ResponseService.generate_sales_response()
  -> WhatsAppCloudAPI.send_whatsapp_message()
  -> WhatsAppCloudAPI.send_whatsapp_image()
```

## Modules

```text
app/
  routers/
    webhook.py                  # FastAPI webhook controller
  services/
    preprocessing_service.py    # text cleaning, Hinglish normalization, keyword extraction
    llm_service.py              # OpenAI calls and strict JSON intent extraction
    search_service.py           # dynamic MongoDB product search
    response_service.py         # sales response generation wrapper
    commerce_ai_service.py      # orchestrator
    whatsapp_cloud_api.py       # WhatsApp text and image senders
  schemas/
    ai.py                       # AI-layer request/response contracts
```

## Sample MongoDB Schema

```json
{
  "products": {
    "id": 1,
    "store_id": 1,
    "category_id": 2,
    "name": "Black Cotton T-Shirt",
    "description": "Soft breathable cotton t-shirt for daily wear.",
    "price": 499,
    "stock": 18,
    "image_url": "https://res.cloudinary.com/demo/image/upload/products/black-tshirt.jpg",
    "image_public_id": "products/black-tshirt",
    "is_active": true,
    "discount": "10% off",
    "created_at": "2026-04-08T09:00:00Z",
    "updated_at": "2026-04-08T09:00:00Z"
  },
  "categories": {
    "id": 2,
    "store_id": 1,
    "name": "T-Shirts"
  }
}
```

Recommended indexes:

```python
products.create_index([("store_id", 1), ("is_active", 1)])
products.create_index([("store_id", 1), ("name", 1)])
products.create_index([("category_id", 1)])
products.create_index([("name", "text"), ("description", "text")])
```

## Intent Extraction Prompt

The exact prompt lives in `app/services/ai_prompts.py` as `INTENT_EXTRACTION_SYSTEM_PROMPT` and `INTENT_EXTRACTION_USER_PROMPT`.

Output shape:

```json
{
  "intent": "browse",
  "products": [
    {
      "name": "t-shirt",
      "category": "t-shirts"
    }
  ],
  "filters": {
    "price_range": {
      "min": null,
      "max": 500
    },
    "color": "black",
    "brand": "",
    "size": "",
    "gender": ""
  },
  "confidence": 0.86
}
```

## Response Generation Prompt

The exact prompt lives in `app/services/ai_prompts.py` as `SALES_RESPONSE_SYSTEM_PROMPT` and `SALES_RESPONSE_USER_PROMPT`.

It instructs the model to behave like a senior retail sales expert, keep WhatsApp responses short, avoid unsupported claims, use emojis sparingly, include CTAs, and include image URLs only when product data provides them.

## Example Input and Output

Input WhatsApp text:

```text
Mujhe sasta black tshirt dikhao under 500
```

Preprocessed:

```json
{
  "cleaned_text": "affordable black t-shirt show under 500",
  "detected_language": "hinglish",
  "keywords": ["affordable", "black", "t-shirt", "show", "under", "500"]
}
```

Product search result:

```json
[
  {
    "id": 1,
    "name": "Black Cotton T-Shirt",
    "price": 499,
    "description": "Soft breathable cotton t-shirt for daily wear.",
    "image_url": "https://res.cloudinary.com/demo/image/upload/products/black-tshirt.jpg",
    "discount": "10% off",
    "category": "T-Shirts",
    "stock": 18
  }
]
```

Generated WhatsApp response:

```text
Hey! I found a solid budget pick for you:

Black Cotton T-Shirt - Rs. 499
Soft cotton, easy daily wear, and it fits your under-500 budget. 10% off is available too.
Image: https://res.cloudinary.com/demo/image/upload/products/black-tshirt.jpg

Want me to help you place the order?
```

If no products match:

```text
I could not find a close match for t-shirt right now. Could you share your preferred budget, size, or color so I can narrow it down?
```
