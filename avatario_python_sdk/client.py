import asyncio
import requests
import threading
import numpy as np
import multiprocessing
from livekit import rtc
import datetime
from datetime import timezone

AVATARIO_BASE_URL = "https://app.onezot.work/api/sdk"

class Avatario:
    """
    Avatario client for audio and video communication over LiveKit.
    
    This class provides methods to connect to a LiveKit room, send audio data,
    and control media playback with interrupt/resume functions.
    
    Attributes:
        api_key (str): API key for authentication.
        room_name (str): Name of the LiveKit room to connect to.
    """

    def __init__(self, api_key: str, room_name: str):
        """
        Initialize a new Avatario client.
        
        Args:
            api_key (str): API key for authentication.
            room_name (str): Name of the LiveKit room to connect to.
        """
        self.api_key = api_key
        self.room_name = room_name
        self.room = None
        self.ipc_data = {
            "audio_queue": asyncio.Queue(),
            "interrupt_signal": asyncio.Event(),
            "kill_signal": asyncio.Event(),
            "video_worker_id": "video-gen",
        }

    def initialize(self):
        """
        Initialize the connection to the LiveKit room.
        
        This method connects the client to the specified room, sets up event handlers,
        and starts background tasks for handling filler content and sending data.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """

        asyncio.create_task(self._async_initialize())

    async def _async_initialize(self):
        """
        Asynchronous implementation of initialize method.
        Invoks a lambda function that returns the url and token for a participant
        to join the livekit room that is running the whole Avatario backend

        """
        global AVATARIO_BASE_URL
        response = requests.post(
            f"{AVATARIO_BASE_URL}/get-token-onezot",
            headers={"x-api-key": self.api_key},
            json={
                "local_identity": "onezot_agent",
                "room_name": self.room_name
            }
        )
        
        token = response.json()["token"]
        url = response.json()["url"]
        
        # Connect the participant to the room
        self.room = rtc.Room()
        await self.room.connect(url, token)
        
        asyncio.create_task(self.send_data())

    async def send_data(self):
        """
        Send audio data to the video worker using data channels.
        """
        while True:
            if self.ipc_data["kill_signal"].is_set():
                break

            if not self.ipc_data["interrupt_signal"].is_set():
                audio_frame = await self.ipc_data["audio_queue"].get()
                np_arr = np.frombuffer(audio_frame.data, dtype=np.int16)
                await self.room.local_participant.publish_data(
                    np_arr.tobytes(),
                    reliable=True,
                    destination_identities=[
                        self.ipc_data["video_worker_id"]
                    ],
                    topic="audio-data",
                )
            else:
                await asyncio.sleep(0.01)

    def send_audio(self, data):
        """
        Send audio data to be processed.
        
        Args:
            data: Audio frame data to be sent.
        """
        self.ipc_data["audio_queue"].put_nowait(data)

    async def send_rpc(self, data: str):
        """
        Send RPC message to the video worker.
        
        Args:
            data (string): RPC data to send.
        """
        await self.room.local_participant.perform_rpc(
            destination_identity=self.ipc_data["video_worker_id"],
            method="playout_state",
            payload=data,
        )

    def clear_queue(self):
        """
        Clear the audio queue.
        
        Internal use only.
        """
        while True:
            try:
                _ = self.ipc_data["audio_queue"].get_nowait()
            except:
                break

    def resume(self):
        """
        Resume media playback after it was interrupted.
        
        This method signals the video worker to resume playback and resets the 
        interrupt signal.
        """
        if self.ipc_data["interrupt_signal"].is_set():
            self.ipc_data["interrupt_signal"].clear()
            asyncio.create_task(self.send_rpc("resume"))
            print(f"resume rpc called at: {datetime.datetime.now(timezone.utc)}")
       
    def interrupt(self):
        """
        Interrupt current media playback.
        
        This method signals the video worker to interrupt playback and clears
        the audio queue.
        """
        self.ipc_data["interrupt_signal"].set()
        asyncio.create_task(self.send_rpc("interrupt"))
        self.clear_queue()
        print(f"queue cleared at: {datetime.datetime.now(timezone.utc)}, {self.ipc_data['audio_queue'].qsize()}")

    async def close(self):
        """
        Clean up resources when the object is destroyed.
        """
        self.ipc_data["kill_signal"].set()
        self.clear_queue()


