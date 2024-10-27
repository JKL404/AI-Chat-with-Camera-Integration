import asyncio
import os
from groq import AsyncGroq
from anthropic import AnthropicBedrock
import streamlit as st
from PIL import Image
import io
import base64
from dotenv import load_dotenv

load_dotenv()


def resize_image(image_base64, max_size=(800, 800), max_bytes=4 * 1024 * 1024):
    # Decode the base64 image
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data))

    # Resize the image
    image.thumbnail(max_size, Image.LANCZOS)

    # Convert the image back to base64 and check size
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    resized_image_data = buffered.getvalue()

    # If the image is still too large, reduce quality
    quality = 95
    while len(resized_image_data) > max_bytes and quality > 10:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=quality)
        resized_image_data = buffered.getvalue()
        quality -= 5

    resized_image_base64 = base64.b64encode(resized_image_data).decode('utf-8')

    return resized_image_base64

def prepare_messages_and_prompt(prompt, image_base64=None, language="English"):
    system_prompt_text = {
        "English": "You are an AI Expert chatting with a person with a live camera feed. Track each emotion and reply based on it. Do not explain each image every time.",
        "Nepali": "तपाईं एक AI विशेषज्ञ हुनुहुन्छ जसले प्रत्यक्ष क्यामेरा फिडको साथ व्यक्तिसँग कुराकानी गर्दै हुनुहुन्छ। प्रत्येक भावना ट्र्याक गर्नुहोस् र त्यसको आधारमा जवाफ दिनुहोस्। प्रत्येक पटक छविको व्याख्या नगर्नुहोस्।",
        "Hindi": "आप एक AI विशेषज्ञ हैं जो लाइव कैमरा फीड के सथ एक व्यक्ति से चैट कर रह��� हैं। प्रत्येक भावना को ट्रैक करें और उसके आधार पर उत्तर दें। हर बार छवि की व्याख्या न करें।",
        "Other": "You are an AI Expert chatting with a person with a live camera feed. Track each emotion and reply based on it. Do not explain each image every time."
    }

    system_prompt = system_prompt_text.get(language, system_prompt_text["English"])

    messages = []
    for message in st.session_state.chat_history:
        messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    if image_base64:
        messages[-1]["content"] += f" [Image: {image_base64}]"

    return messages, system_prompt

async def get_llm_response(prompt, image_base64=None, language="English", use_groq=True):
    # Resize the image if provided
    if image_base64:
        image_base64 = resize_image(image_base64)

    if use_groq:
        return await get_groq_response(prompt, image_base64, language)
    else:
        return get_anthropic_response(prompt, image_base64, language)

async def get_groq_response(prompt, image_base64=None, language="English"):
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    messages, system_prompt = prepare_messages_and_prompt(prompt, image_base64, language)

    # If an image is included, prepend the system prompt to the user's message with clear indication
    if image_base64:
        messages[-1] = {
            "role": "user",
            "content": [
                {"type": "text", "text": f"System Prompt: {system_prompt}\nUser Message: {messages[-1]['content']}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }
    else:
        # Add the system prompt as a separate message if no image is included
        messages.insert(0, {"role": "system", "content": system_prompt})

    stream = await client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=messages,
        # temperature=1,
        # max_tokens=1024,
        # top_p=1,
        stream=True
    )

    # Create a placeholder for the chat response
    chat_placeholder = st.empty()

    # Accumulate chunks to form complete sentences and the full response
    full_response = ""
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content is not None:  # Check if content is not None
            full_response += content
            chat_placeholder.markdown(f"**Assistant:** {full_response}")

    return full_response

def get_anthropic_response(prompt, image_base64=None, language="English"):
    client = AnthropicBedrock(aws_region="us-west-2")
    messages, system_prompt = prepare_messages_and_prompt(prompt, image_base64, language)

    # Convert messages to the format required by Anthropic
    anthropic_messages = []
    for message in messages:
        anthropic_messages.append({
            "role": message["role"],
            "content": [{"type": "text", "text": message["content"]}]
        })

    response = client.messages.create(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=1000,
        messages=anthropic_messages,
        system=[{"type": "text", "text": system_prompt}],
        stream=True
    )

    # Create a placeholder for the chat response
    chat_placeholder = st.empty()

    # Accumulate chunks to form complete sentences and the full response
    full_response = ""
    for chunk in response:
        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
            full_response += chunk.delta.text
            chat_placeholder.markdown(f"**Assistant:** {full_response}")

    return full_response
