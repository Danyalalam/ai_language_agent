/**
 * Browser client for the live German voice conversation.
 *
 * Talks to the FastAPI `/api/voice/live` WebSocket which relays to Azure
 * VoiceLive (see `app/services/voicelive_bridge.py`).
 *
 *   Browser -> Server : binary frames, raw PCM16 mono @ 24 kHz mic audio.
 *   Server -> Browser : binary frames, raw PCM16 mono @ 24 kHz to play back;
 *                       text frames (JSON) for status / speech_started /
 *                       transcript / error events.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const SAMPLE_RATE = 24000;
const CAPTURE_BUFFER_SIZE = 4096;

export type VoiceState =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'ready'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'error';

export interface VoiceLiveHandlers {
  onStateChange?: (state: VoiceState) => void;
  onTranscript?: (role: string, text: string) => void;
  onError?: (message: string) => void;
}

function buildWebSocketUrl(): string {
  // http://host/api -> ws://host/api/voice/live  (and https -> wss)
  const wsBase = API_BASE_URL.replace(/^http/, 'ws').replace(/\/$/, '');
  return `${wsBase}/voice/live`;
}

export class VoiceLiveClient {
  private ws: WebSocket | null = null;
  private handlers: VoiceLiveHandlers;

  // Capture
  private captureCtx: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;

  // Playback
  private playbackCtx: AudioContext | null = null;
  private nextPlayTime = 0;
  private scheduledSources: Set<AudioBufferSourceNode> = new Set();

  constructor(handlers: VoiceLiveHandlers = {}) {
    this.handlers = handlers;
  }

  private setState(state: VoiceState) {
    this.handlers.onStateChange?.(state);
  }

  async start(): Promise<void> {
    this.setState('connecting');

    // Create the playback context synchronously, while we are still inside the
    // user's click gesture. If we created it after the awaits below, the browser
    // would start it "suspended" and silently drop all scheduled audio.
    this.playbackCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
    this.nextPlayTime = 0;
    if (this.playbackCtx.state === 'suspended') {
      await this.playbackCtx.resume();
    }

    // Request the mic first so a denial fails fast before we open the socket.
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    await this.openSocket();
    this.startCapture();
  }

  private openSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(buildWebSocketUrl());
      ws.binaryType = 'arraybuffer';
      this.ws = ws;

      ws.onopen = () => {
        this.setState('connected');
        resolve();
      };
      ws.onerror = () => {
        this.handlers.onError?.('WebSocket connection error');
        this.setState('error');
        reject(new Error('WebSocket connection error'));
      };
      ws.onclose = () => {
        if (this.ws) {
          this.setState('idle');
        }
      };
      ws.onmessage = (event) => this.handleMessage(event);
    });
  }

  private handleMessage(event: MessageEvent) {
    if (event.data instanceof ArrayBuffer) {
      this.enqueuePlayback(event.data);
      return;
    }
    let msg: Record<string, unknown>;
    try {
      msg = JSON.parse(event.data as string);
    } catch {
      return; // Ignore non-JSON text frames.
    }

    switch (msg.type) {
      case 'status':
        this.setState(msg.state as VoiceState);
        break;
      case 'speech_started':
        // Barge-in: user is talking over the assistant. Drop queued audio.
        this.flushPlayback();
        break;
      case 'transcript':
        this.handlers.onTranscript?.(msg.role as string, msg.text as string);
        break;
      case 'error':
        this.handlers.onError?.(msg.message as string);
        this.setState('error');
        break;
    }
  }

  // --- Capture: mic -> PCM16 -> WebSocket -------------------------------

  private startCapture() {
    const ctx = new AudioContext({ sampleRate: SAMPLE_RATE });
    this.captureCtx = ctx;
    this.sourceNode = ctx.createMediaStreamSource(this.mediaStream!);
    this.processorNode = ctx.createScriptProcessor(CAPTURE_BUFFER_SIZE, 1, 1);

    this.processorNode.onaudioprocess = (e) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const input = e.inputBuffer.getChannelData(0);
      this.ws.send(floatTo16BitPCM(input));
    };

    this.sourceNode.connect(this.processorNode);
    // Route through a muted gain node so onaudioprocess fires without echoing
    // the mic to the speakers.
    const mute = ctx.createGain();
    mute.gain.value = 0;
    this.processorNode.connect(mute);
    mute.connect(ctx.destination);
  }

  // --- Playback: PCM16 -> scheduled AudioBufferSourceNodes --------------

  private enqueuePlayback(data: ArrayBuffer) {
    const ctx = this.playbackCtx;
    if (!ctx) return;

    // A context can drift back to "suspended" (e.g. tab backgrounded); resume
    // so scheduled audio actually plays instead of being silently dropped.
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }

    // Int16Array requires an even byte length; a PCM16 chunk should always be
    // even, but guard against a truncated frame rather than throwing.
    const usableBytes = data.byteLength - (data.byteLength % 2);
    const int16 = new Int16Array(data, 0, usableBytes / 2);
    if (int16.length === 0) return;

    const buffer = ctx.createBuffer(1, int16.length, SAMPLE_RATE);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < int16.length; i++) {
      channel[i] = int16[i] / 32768;
    }

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    const now = ctx.currentTime;
    const startAt = Math.max(now, this.nextPlayTime);
    source.start(startAt);
    this.nextPlayTime = startAt + buffer.duration;

    this.scheduledSources.add(source);
    source.onended = () => this.scheduledSources.delete(source);
  }

  private flushPlayback() {
    for (const source of this.scheduledSources) {
      try {
        source.stop();
      } catch {
        // already stopped
      }
    }
    this.scheduledSources.clear();
    this.nextPlayTime = this.playbackCtx?.currentTime ?? 0;
  }

  async stop(): Promise<void> {
    const ws = this.ws;
    this.ws = null; // signal onclose that this is intentional

    this.processorNode?.disconnect();
    this.sourceNode?.disconnect();
    this.processorNode = null;
    this.sourceNode = null;

    this.mediaStream?.getTracks().forEach((t) => t.stop());
    this.mediaStream = null;

    this.flushPlayback();

    if (this.captureCtx) {
      await this.captureCtx.close().catch(() => {});
      this.captureCtx = null;
    }
    if (this.playbackCtx) {
      await this.playbackCtx.close().catch(() => {});
      this.playbackCtx = null;
    }

    if (ws && ws.readyState <= WebSocket.OPEN) {
      ws.close();
    }
    this.setState('idle');
  }
}

function floatTo16BitPCM(input: Float32Array): ArrayBuffer {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output.buffer;
}
