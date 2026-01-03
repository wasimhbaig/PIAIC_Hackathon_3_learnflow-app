/**
 * Custom hook for WebSocket connection to LearnFlow chat
 */
import { useEffect, useState, useCallback, useRef } from 'react';

interface Message {
  type: string;
  content: string;
  agent?: string;
  metadata?: any;
  timestamp?: string;
}

interface UseWebSocketReturn {
  messages: Message[];
  sendMessage: (content: string) => void;
  isConnected: boolean;
  error: string | null;
}

export const useWebSocket = (studentId: string, token: string): UseWebSocketReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!studentId || !token) return;

    // Construct WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/chat/ws?student_id=${studentId}`;

    // Create WebSocket connection
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message: Message = JSON.parse(event.data);
        setMessages((prev) => [...prev, message]);
      } catch (err) {
        console.error('Failed to parse message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [studentId, token]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = {
        type: 'message',
        content,
        metadata: {}
      };

      wsRef.current.send(JSON.stringify(message));

      // Add user message to local state
      setMessages((prev) => [
        ...prev,
        {
          type: 'user',
          content,
          timestamp: new Date().toISOString()
        }
      ]);
    } else {
      setError('WebSocket not connected');
    }
  }, []);

  return {
    messages,
    sendMessage,
    isConnected,
    error
  };
};
