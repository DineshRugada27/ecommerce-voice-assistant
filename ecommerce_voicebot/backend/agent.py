# This code launches a LiveKit Agent Worker that joins a LiveKit room
# and acts as a voice AI assistant
# Listens to user speech (STT via OpenAI Whisper)
# Thinks using OpenAI LLM (GPT-4o-mini) with RAG
# Speaks back using Cartesia TTS
# Detects when user finishes speaking (VAD + turn detection)
# Applies noise cancellation
# Interacts with users in real-time over LiveKit
# Uses RAG to answer questions from product catalog/documentation

import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    llm
)
from livekit.plugins import (
    openai,
    cartesia,
    noise_cancellation,
    silero
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from rag_system import get_rag_system

load_dotenv()


class Assistant(Agent):
    def __init__(self):
        # Initialize RAG system
        self.rag = get_rag_system()

        instructions = (
            "You are a friendly and helpful e-commerce voice shopping "
            "assistant for Voice Commerce. Your role is to help customers "
            "with their shopping needs.\n\n"
            "Your capabilities include:\n"
            "1. Product Search & Discovery: Help customers find products "
            "based on their needs, preferences, and queries.\n"
            "2. Product Information: Provide detailed information about "
            "products including features, specifications, prices, "
            "availability, and reviews.\n"
            "3. Shopping Assistance: Help with product comparisons, "
            "recommendations, and shopping guidance.\n"
            "4. Order Management: Assist with order status, tracking, "
            "returns, and refunds.\n"
            "5. General Shopping Help: Answer questions about shipping, "
            "delivery, payment methods, promotions, and policies.\n\n"
            "Guidelines:\n"
            "- Always be conversational, friendly, and helpful\n"
            "- Keep responses concise since this is a voice interface\n"
            "- Use the provided product catalog/documentation context when "
            "available\n"
            "- For product-related queries, use the document context to give "
            "accurate information\n"
            "- For general shopping questions, use your knowledge of "
            "e-commerce best practices\n"
            "- If you don't have specific product information, acknowledge it "
            "and offer to help in other ways\n"
            "- Always maintain a professional yet warm tone\n\n"
            "The product catalog and documentation context will be provided "
            "when relevant to answer product-specific questions."
        )

        super().__init__(instructions=instructions)

    async def on_user_turn_completed(
        self, chat_ctx: llm.ChatContext, *, new_message: llm.ChatMessage
    ) -> None:
        """Intercept user messages to add RAG context before LLM processing."""
        user_text = ""
        if new_message.content:
            # Extract text from message content
            if isinstance(new_message.content, list):
                user_text = " ".join([
                    str(item) for item in new_message.content
                    if isinstance(item, str)
                ])
            elif isinstance(new_message.content, str):
                user_text = new_message.content

        if not user_text:
            return

        # Check if query is relevant to products/catalog in document
        is_relevant = self.rag.is_relevant_query(user_text)

        if is_relevant:
            # Retrieve relevant product/catalog context from document
            relevant_chunks = self.rag.retrieve(user_text, top_k=3)

            if relevant_chunks:
                # Build context string for product information
                context = "\n\n--- Product Catalog & Information ---\n\n"
                for i, chunk in enumerate(relevant_chunks, 1):
                    section = f"[Product Information Section {i}]\n"
                    context += f"{section}{chunk}\n\n"
                context += "--- End of Product Information ---\n\n"

                # Add context as a system message
                context_msg = (
                    "The user is asking about products or shopping-related "
                    "information. Use the following product catalog and "
                    "documentation context to provide accurate, helpful "
                    "answers about products, features, prices, availability, "
                    "or shopping-related information:\n\n"
                    f"{context}"
                    "Be specific and helpful. If the information isn't in "
                    "the context, acknowledge it and offer general guidance."
                )
                context_message = llm.ChatMessage(
                    role="system",
                    content=[context_msg]
                )

                # Insert context message before the user message
                try:
                    msg_index = chat_ctx.items.index(new_message)
                    chat_ctx.items.insert(msg_index, context_message)
                except ValueError:
                    # If message not found, prepend context
                    chat_ctx.items.insert(-1, context_message)
        else:
            # For general shopping questions, use e-commerce knowledge
            context_msg = (
                "The user's question is about general shopping, e-commerce, "
                "or customer service topics. Use your knowledge of "
                "e-commerce best practices, shopping assistance, order "
                "management, shipping, returns, and customer service to "
                "provide helpful, conversational answers. Be friendly and "
                "professional. If you can't find specific product "
                "information, offer to help in other ways or suggest "
                "alternatives."
            )
            context_message = llm.ChatMessage(
                role="system",
                content=[context_msg]
            )
            try:
                msg_index = chat_ctx.items.index(new_message)
                chat_ctx.items.insert(msg_index, context_message)
            except ValueError:
                chat_ctx.items.insert(-1, context_message)


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(
            model="sonic-2",
            voice="f786b574-daa5-4673-aa0c-cbe3e8534c02",
        ),
        # tools
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Wait so browser can subscribe to agent's audio track
    await asyncio.sleep(2)

    await session.generate_reply(
        instructions=(
            "Welcome to Voice Commerce! I'm your personal shopping "
            "assistant. I can help you find products, answer questions "
            "about items, assist with orders, and guide you through your "
            "shopping experience. What would you like to shop for today?"
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )
