import { useEffect, useRef, useState, useCallback } from 'react';

export const useWebSocket = (userId, onMessage) => {
    const ws = useRef(null);
    const [isConnected, setIsConnected] = useState(false);
    const reconnectTimeout = useRef(null);
    const userIdRef = useRef(userId);
    const onMessageRef = useRef(onMessage);

    // Keep refs up to date
    useEffect(() => {
        userIdRef.current = userId;
        onMessageRef.current = onMessage;
    });

    const connect = useCallback(() => {
        if (!userIdRef.current) return;

        // Close existing
        if (ws.current) {
            ws.current.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
        // In dev, Vite proxy might handle it, but for WS usually need explicit port if different
        // Assuming API_URL might be different
        const wsUrl = `${protocol}//${host}/ws/dashboard/${userIdRef.current}`;

        console.log('Connecting WS:', wsUrl);
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WS Connected');
            setIsConnected(true);
            // Clear any reconnect timeout if we connected successfully
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
                reconnectTimeout.current = null;
            }
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (onMessageRef.current) {
                    onMessageRef.current(data);
                }
            } catch (err) {
                console.error('WS Message Parse Error:', err);
            }
        };

        socket.onclose = () => {
            console.log('WS Disconnected');
            setIsConnected(false);
            ws.current = null;

            // Reconnect logic
            if (!reconnectTimeout.current) {
                reconnectTimeout.current = setTimeout(() => {
                    reconnectTimeout.current = null;
                    connect();
                }, 3000); // Retry every 3s
            }
        };

        socket.onerror = (err) => {
            console.error('WS Error:', err);
            socket.close();
        };

        ws.current = socket;
    }, []);

    useEffect(() => {
        if (userId) {
            connect();
        }
        return () => {
            if (ws.current) {
                ws.current.close();
            }
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
        };
    }, [userId, connect]);

    return { isConnected };
};
