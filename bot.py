import os
import sys
import uuid
import asyncio
import aiohttp
from loguru import logger
from runner import configure
from datetime import datetime
from dotenv import load_dotenv
from calendar_service import CalendarService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import LLMMessagesFrame
from openai.types.chat import ChatCompletionToolParam
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai import OpenAILLMContext, OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

load_dotenv(override=True)
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

calendar_service = CalendarService()

async def main():
    async with aiohttp.ClientSession() as session:
        (room_url, token) = await configure(session)

        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new session with ID: {session_id}")

        transport = DailyTransport(
            room_url,
            token,
            "Chatbot",
            DailyParams(
                audio_out_enabled=True,
                camera_out_enabled=True,
                camera_out_width=1024,
                camera_out_height=576,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,
            ),
        )

        tools = [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "create_calendar_event",
                    "description": "Create a new calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the event given the context of the conversation"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the event given the context of the conversation"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO format (e.g., 2024-03-20T14:00:00) in the user's timezone"
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee email addresses"
                            }
                        },
                        "required": ["title", "start_time"],
                    },
                },
            ),
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "get_free_availability",
                    "description": "Get free time slots in the calendar for a specified time range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO format (e.g., 2024-03-20T09:00:00) in the user's timezone"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time in ISO format (e.g., 2024-03-20T17:00:00) in the user's timezone"
                            }
                        },
                        "required": ["start_time", "end_time"],
                    },
                },
            ),
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "update_calendar_event",
                    "description": "Update an existing calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {
                                "type": "string",
                                "description": "ID of the event to update"
                            },
                            "title": {
                                "type": "string",
                                "description": "New title of the event (optional)"
                            },
                            "description": {
                                "type": "string",
                                "description": "New description of the event (optional)"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "New start time in ISO format (e.g., 2024-03-20T14:00:00) in the user's timezone"
                            }
                        },
                        "required": ["event_id"],  # Remove start_time from required fields
                    },
                },
            ),
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "cancel_calendar_event",
                    "description": "Cancel/delete an existing calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {
                                "type": "string",
                                "description": "ID of the event to cancel"
                            }
                        },
                        "required": ["event_id"],
                    },
                },
            ),
        ]

        current_time = datetime.now()
        name = "Matthew"
        email = "matthew@gmail.com"
        location = "Melbourne, Australia"

        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful LLM in a WebRTC call. 
                Your goal is to demonstrate your capabilities in a succinct way. 
                Your output will be converted to audio so don't include special characters in your answers. 
                Respond to what the user said in a creative and helpful way.

                Instructions:
                1. If the user asks for availability, always use the get_free_availability function. When you respond to them, only give them times between 9am and 5pm where there is availability.
                2. If the user asks to create a calendar event, use the create_calendar_event function. Create it for 30 minutes. Do not add any other attendees.
                3. If the user asks to update a calendar event, use the update_calendar_event function.
                4. If the user asks to cancel a calendar event, use the cancel_calendar_event function.
                
                You don't need to mention these details, but so that you have them for your own reference.
                1. The current date and time is {current_time.strftime('%B %d, %Y %I:%M %p')} - and their current timezone is AEDT (Sydney time).
                2. The user's name is {name}.
                3. The user's email is {email}.
                4. The user is located in {location}.
                """,
            },
            {
                "role": "system",
                "content": "Start by introducing yourself as a calendar assistant and ask the user what they would like to do."
            }
        ]

        context = OpenAILLMContext(messages, tools)

        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"),
            voice_id="421b3369-f63f-4b03-8980-37a44df1d4e8"
        )

        llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"), 
            model="gpt-4"
        )

        # Register calendar functions with their start callbacks
        llm.register_function(
            "create_calendar_event", 
            calendar_service.handle_create_calendar_event, 
            start_callback=calendar_service.start_create_calendar_event
        )
        llm.register_function(
            "get_free_availability", 
            calendar_service.handle_get_free_availability, 
            start_callback=calendar_service.start_get_free_availability
        )
        llm.register_function(
            "update_calendar_event", 
            calendar_service.handle_update_calendar_event, 
            start_callback=calendar_service.start_update_calendar_event
        )
        llm.register_function(
            "cancel_calendar_event", 
            calendar_service.handle_cancel_calendar_event, 
            start_callback=calendar_service.start_cancel_calendar_event
        )

        context_aggregator = llm.create_context_aggregator(context)

        pipeline = Pipeline(
            [
                transport.input(),
                context_aggregator.user(),
                llm,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ]
        )

        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))


        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            await transport.capture_participant_transcription(participant["id"])
            await task.queue_frames([LLMMessagesFrame(messages)])

        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())