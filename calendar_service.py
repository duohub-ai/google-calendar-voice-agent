import os
import asyncio
from loguru import logger
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pipecat.frames.frames import TTSSpeakFrame

class CalendarService:
    def __init__(self):
        self.refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.aedt = ZoneInfo("Australia/Sydney")

    # Start callbacks
    async def start_get_free_availability(self, function_name, llm, context):
        """Push a frame to the LLM; this is handy when the LLM response might take a while."""
        await llm.push_frame(TTSSpeakFrame("Sure. Just a moment."))
        logger.debug(f"Starting get_free_availability with function_name: {function_name}")

    async def start_create_calendar_event(self, function_name, llm, context):
        """Push a frame to the LLM while creating calendar event"""
        await llm.push_frame(TTSSpeakFrame("Scheduling your event now."))
        logger.debug(f"Starting create_calendar_event with function_name: {function_name}")

    async def start_update_calendar_event(self, function_name, llm, context):
        """Push a frame to the LLM while updating calendar event"""
        await llm.push_frame(TTSSpeakFrame("Updating the event."))
        logger.debug(f"Starting update_calendar_event with function_name: {function_name}")

    async def start_cancel_calendar_event(self, function_name, llm, context):
        """Push a frame to the LLM while canceling calendar event"""
        await llm.push_frame(TTSSpeakFrame("Just a moment, working on it."))
        logger.debug(f"Starting cancel_calendar_event with function_name: {function_name}")

    # Handler functions
    async def handle_get_calendar_events(self, function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"get_calendar_events called with args: {args}")
        try:
            events = await self.get_calendar_events()
            await result_callback({
                "events": events,
                "count": len(events) if events else 0
            })
        except Exception as e:
            logger.error(f"Error in get_calendar_events: {str(e)}")
            await result_callback({
                "events": f"Sorry, I encountered an error: {str(e)}",
                "count": 0
            })

    async def handle_create_calendar_event(self, function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"create_calendar_event called with args: {args}")
        result = await self.create_calendar_event(
            title=args['title'],
            start_time_str=args['start_time'],
            description=args.get('description', ''),
            attendees=args.get('attendees')
        )
        await result_callback(result)

    async def handle_get_free_availability(self, function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"get_free_availability called with args: {args}")
        result = await self.get_free_availability(
            start_time_str=args['start_time'],
            end_time_str=args['end_time']
        )
        await result_callback(result)

    async def handle_update_calendar_event(self, function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"update_calendar_event called with args: {args}")
        result = await self.update_calendar_event(
            event_id=args['event_id'],
            title=args.get('title'),
            description=args.get('description'),
            start_time_str=args.get('start_time')
        )
        await result_callback(result)

    async def handle_cancel_calendar_event(self, function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"cancel_calendar_event called with args: {args}")
        result = await self.cancel_calendar_event(event_id=args['event_id'])
        await result_callback(result)

    def get_calendar_service(self):
        logger.debug(f"Starting get_calendar_service with token: {self.refresh_token[:10]}...")
        try:
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            logger.debug("Created credentials object")
            
            service = build('calendar', 'v3', credentials=creds)
            logger.debug("Built calendar service successfully")
            return service
        except Exception as e:
            logger.error(f"Error in get_calendar_service: {str(e)}", exc_info=True)
            raise

    async def get_calendar_events(self):
        try:
            service = self.get_calendar_service()
            events_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: service.events().list(
                    calendarId='primary',
                    maxResults=10,
                    singleEvents=True,
                    orderBy='startTime',
                    timeMin=datetime.utcnow().isoformat() + 'Z'
                ).execute()
            )
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}")
            raise

    async def create_calendar_event(self, title, start_time_str, description='', attendees=None):
        try:
            service = self.get_calendar_service()
            
            # Parse the start time
            start_time = self._parse_start_time(start_time_str)
            end_time = start_time + timedelta(minutes=30)
            
            # Convert to UTC for the API
            start_time_utc = start_time.astimezone(timezone.utc)
            end_time_utc = end_time.astimezone(timezone.utc)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time_utc.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time_utc.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
                event['guestsCanModify'] = True
            
            event = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
            )
            return {
                "success": True,
                "event_id": event.get('id'),
                "message": f"Event '{title}' scheduled successfully"
            }
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return {
                "success": False,
                "event_id": None,
                "message": f"Failed to create event: {str(e)}"
            }

    async def get_free_availability(self, start_time_str, end_time_str):
        try:
            service = self.get_calendar_service()
            
            start_time = datetime.fromisoformat(start_time_str).replace(tzinfo=self.aedt)
            end_time = datetime.fromisoformat(end_time_str).replace(tzinfo=self.aedt)
            
            start_time_utc = start_time.astimezone(timezone.utc)
            end_time_utc = end_time.astimezone(timezone.utc)
            
            body = {
                'timeMin': start_time_utc.isoformat(),
                'timeMax': end_time_utc.isoformat(),
                'items': [{'id': 'primary'}]
            }
            
            freebusy_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: service.freebusy().query(body=body).execute()
            )
            
            free_slots = self._process_freebusy_response(freebusy_response, start_time, end_time)
            
            if free_slots:
                free_slots_text = "\n".join([
                    f"- Available from {slot['start'].strftime('%I:%M %p')} to {slot['end'].strftime('%I:%M %p')}"
                    for slot in free_slots
                ])
                return {
                    "available_slots": free_slots_text,
                    "count": len(free_slots)
                }
            else:
                return {
                    "available_slots": "No free time slots found in the specified range",
                    "count": 0
                }
        except Exception as e:
            logger.error(f"Error getting free availability: {str(e)}")
            return {
                "available_slots": f"Sorry, I encountered an error: {str(e)}",
                "count": 0
            }

    async def update_calendar_event(self, event_id, title=None, description=None, start_time_str=None):
        try:
            service = self.get_calendar_service()
            
            # Get existing event
            event = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: service.events().get(calendarId='primary', eventId=event_id).execute()
            )
            
            # Update the event details
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
                
            # Only update time if start_time is provided
            if start_time_str:
                start_time = self._parse_start_time(start_time_str)
                end_time = start_time + timedelta(minutes=30)
                
                event.update({
                    'start': {
                        'dateTime': start_time.astimezone(timezone.utc).isoformat(),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': end_time.astimezone(timezone.utc).isoformat(),
                        'timeZone': 'UTC',
                    },
                })

            updated_event = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: service.events().update(
                    calendarId='primary',
                    eventId=event_id,
                    body=event,
                    sendUpdates='all'
                ).execute()
            )
            
            return {
                "success": True,
                "event_id": updated_event.get('id'),
                "message": "Event updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating calendar event: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update event: {str(e)}"
            }

    async def cancel_calendar_event(self, event_id):
        try:
            service = self.get_calendar_service()
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: service.events().delete(
                    calendarId='primary',
                    eventId=event_id,
                    sendUpdates='all'
                ).execute()
            )
            
            return {
                "success": True,
                "message": "Event cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling calendar event: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to cancel event: {str(e)}"
            }

    def _parse_start_time(self, start_time_str):
        now = datetime.now(self.aedt)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if "this afternoon" in start_time_str.lower():
            return today.replace(hour=14, minute=0)
        elif "this week" in start_time_str.lower():
            start_time = today.replace(hour=9, minute=0)
            while start_time.weekday() > 4:
                start_time += timedelta(days=1)
            return start_time
        else:
            return datetime.fromisoformat(start_time_str).replace(tzinfo=self.aedt)

    def _process_freebusy_response(self, freebusy_response, start_time, end_time):
        busy_periods = freebusy_response['calendars']['primary']['busy']
        free_slots = []
        current_time = start_time
        
        for busy in busy_periods:
            busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00')).astimezone(self.aedt)
            busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00')).astimezone(self.aedt)
            
            if current_time < busy_start:
                free_slots.append({
                    'start': current_time,
                    'end': busy_start
                })
            current_time = busy_end
        
        if current_time < end_time:
            free_slots.append({
                'start': current_time,
                'end': end_time
            })
            
        return free_slots
