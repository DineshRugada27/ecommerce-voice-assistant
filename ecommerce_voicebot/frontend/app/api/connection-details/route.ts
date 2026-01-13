import { NextResponse } from 'next/server';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

// NOTE: you are expected to define the following environment variables in `.env.local`:
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

// Backend Flask API URL (fallback)
const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://localhost:5000';

// Track if backend endpoint has been called
let backendEndpointCalled = false;

// don't cache the results
export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }

    // Parse agent configuration from request body (if present)
    let body: any = {};
    try {
      const contentType = req.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const text = await req.text();
        if (text) {
          body = JSON.parse(text);
        }
      }
    } catch (error) {
      // If body parsing fails, continue with empty body
      console.warn('Failed to parse request body:', error);
    }
    const agentName: string = body?.room_config?.agents?.[0]?.agent_name;

    // Try to call backend Flask /getToken endpoint if not called previously
    if (!backendEndpointCalled) {
      try {
        const participantName = 'user';
        const backendUrl = `${BACKEND_API_URL}/getToken?name=${encodeURIComponent(participantName)}`;
        
        const backendResponse = await fetch(backendUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (backendResponse.ok) {
          const backendData = await backendResponse.json();
          backendEndpointCalled = true;
          
          // Return connection details from backend
          const data: ConnectionDetails = {
            serverUrl: LIVEKIT_URL,
            roomName: backendData.room || `voice_assistant_room_${Math.floor(Math.random() * 10_000)}`,
            participantToken: backendData.token,
            participantName: backendData.identity || participantName,
          };
          
          const headers = new Headers({
            'Cache-Control': 'no-store',
          });
          return NextResponse.json(data, { headers });
        }
      } catch (backendError) {
        // If backend call fails, fall through to local token generation
        console.warn('Backend /getToken endpoint not available, using local token generation:', backendError);
      }
    }

    // Fallback to local token generation
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Generate participant token locally
    const participantName = 'user';
    const participantIdentity = `voice_assistant_user_${Math.floor(Math.random() * 10_000)}`;
    const roomName = `voice_assistant_room_${Math.floor(Math.random() * 10_000)}`;

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName,
      agentName
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: participantToken,
      participantName,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  agentName?: string
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (agentName) {
    at.roomConfig = new RoomConfiguration({
      agents: [{ agentName }],
    });
  }

  return at.toJwt();
}
