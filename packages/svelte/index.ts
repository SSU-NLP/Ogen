export type UITree = {
    type: string;
    props?: Record<string, any>;
    children?: UITree[];
} | null;

export interface OgenState {
    status: 'idle' | 'loading' | 'error' | 'success';
    tree: UITree;
    error: string | null;
    connectionStatus?: 'disconnected' | 'connecting' | 'connected' | 'error';
}

export type Listener = (state: OgenState) => void;

export interface ApiResponse {
    source_anchor: string;
    reasoning_mode: string;
    generated_spec: UITree;
    error?: string;
}

export interface ConnectResponse {
    status: 'success' | 'already_connected';
    message: string;
    node_count: number;
}

export interface ConnectResult {
    success: boolean;
    message: string;
    nodeCount?: number;
}

export interface OgenRuntimeOptions {
    connectEndpoint?: string;
    ttlContent?: string;
    autoConnect?: boolean;
}

export class OgenRuntime {
    private endpoint: string;
    private connectEndpoint?: string;
    private listeners: Listener[] = [];
    private state: OgenState = {
        status: 'idle',
        tree: null,
        error: null,
        connectionStatus: 'disconnected'
    };
    private isConnected: boolean = false;

    constructor(endpoint: string, options?: OgenRuntimeOptions) {
        this.endpoint = endpoint;
        this.connectEndpoint = options?.connectEndpoint;

        // autoConnect 옵션이 있고 ttlContent가 있으면 자동 연결
        if (options?.autoConnect && options?.ttlContent && this.connectEndpoint) {
            this.connect(this.connectEndpoint, options.ttlContent).catch(err => {
                console.error('Auto-connect failed:', err);
            });
        }
    }

    subscribe(listener: Listener): () => void {
        this.listeners.push(listener);

        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        }
    }

    private setState(newState: Partial<OgenState>) {
        this.state = { ...this.state, ...newState };
        this.listeners.forEach(listener => listener(this.state));
    }

    async execute(query: string, context: string = "default"): Promise<void> {
        this.setState({ status: 'loading', error: null });

        try {
            const res = await fetch(this.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, context })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText);
            }

            const data: ApiResponse = await res.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.setState({
                status: 'success',
                tree: data.generated_spec
            });
        } catch (error) {
            this.setState({ status: 'error', error: error instanceof Error ? error.message : String(error) });
        }
    }

    async connect(endpoint: string, ttlContent: string): Promise<ConnectResult> {
        this.setState({ connectionStatus: 'connecting' });

        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ttl_content: ttlContent,
                    base_iri: "http://myapp.com/ui/"
                })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText);
            }

            const data: ConnectResponse = await res.json();

            this.isConnected = true;
            this.setState({
                connectionStatus: 'connected'
            });

            return {
                success: true,
                message: data.message,
                nodeCount: data.node_count
            };
        } catch (error) {
            this.isConnected = false;
            this.setState({
                connectionStatus: 'error'
            });

            return {
                success: false,
                message: error instanceof Error ? error.message : String(error)
            };
        }
    }
}

// ===== Chat Runtime Types =====
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    uiTree?: UITree;
    timestamp: Date;
    isStreaming?: boolean;
}

export interface ChatState {
    messages: ChatMessage[];
    status: 'idle' | 'loading' | 'error' | 'success';
    connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
    error: string | null;
}

export type ChatListener = (state: ChatState) => void;

export interface StreamChunk {
    type: 'text' | 'ui' | 'error' | 'done';
    content?: string;
    uiTree?: UITree;
    error?: string;
}

export interface OgenChatRuntimeOptions {
    connectEndpoint?: string;
    ttlContent?: string;
    autoConnect?: boolean;
    enableStreaming?: boolean;
}

// ===== Chat Runtime Class =====
export class OgentRuntime {
    private endpoint: string;
    private connectEndpoint?: string;
    private listeners: ChatListener[] = [];
    private state: ChatState = {
        messages: [],
        status: 'idle',
        connectionStatus: 'disconnected',
        error: null
    };
    private isConnected: boolean = false;
    private enableStreaming: boolean = false;
    private currentStreamingMessageId: string | null = null;

    constructor(endpoint: string, options?: OgenChatRuntimeOptions) {
        this.endpoint = endpoint;
        this.connectEndpoint = options?.connectEndpoint;
        this.enableStreaming = options?.enableStreaming ?? false;

        // Store connection data to avoid repeated connections
        const connectionKey = `ogen_connection_${endpoint}`;

        // autoConnect 옵션이 있고 ttlContent가 있으면 자동 연결
        if (options?.autoConnect && options?.ttlContent && this.connectEndpoint) {
            this.connect(this.connectEndpoint, options.ttlContent).catch(err => {
                console.error('Auto-connect failed:', err);
            });
        }
    }

    subscribe(listener: ChatListener): () => void {
        this.listeners.push(listener);
        // 즉시 현재 상태 전달
        listener(this.state);

        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        }
    }

    private setState(newState: Partial<ChatState>) {
        this.state = { ...this.state, ...newState };
        this.listeners.forEach(listener => listener(this.state));
    }

    private addMessage(message: ChatMessage) {
        this.setState({
            messages: [...this.state.messages, message]
        });
        return message;
    }

    private updateMessage(messageId: string, updates: Partial<ChatMessage>) {
        const messages = this.state.messages.map(msg =>
            msg.id === messageId ? { ...msg, ...updates } : msg
        );
        this.setState({ messages });
    }

    async sendMessage(query: string, context: string = "default"): Promise<void> {
        if (!query.trim() || this.state.connectionStatus !== 'connected') {
            return;
        }

        // 사용자 메시지 추가
        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: query.trim(),
            timestamp: new Date()
        };
        this.addMessage(userMessage);

        // 어시스턴트 메시지 생성 (로딩 상태)
        const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true
        };
        this.addMessage(assistantMessage);
        this.currentStreamingMessageId = assistantMessage.id;

        this.setState({ status: 'loading', error: null });

        try {
            if (this.enableStreaming) {
                await this.executeStreaming(query, context, assistantMessage.id);
            } else {
                await this.executeNonStreaming(query, context, assistantMessage.id);
            }
        } catch (error) {
            this.updateMessage(assistantMessage.id, {
                content: `❌ Error: ${error instanceof Error ? error.message : String(error)}`,
                isStreaming: false
            });
            this.setState({
                status: 'error',
                error: error instanceof Error ? error.message : String(error)
            });
        } finally {
            this.currentStreamingMessageId = null;
        }
    }

    async sendChatMessage(message: string, context: string = "default"): Promise<void> {
        /**
         * Chat 스트리밍 메시지 전송 (SSE 사용)
         * /chat/stream 엔드포인트 사용
         */
        if (!message.trim() || this.state.connectionStatus !== 'connected') {
            return;
        }

        // 사용자 메시지 추가
        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: message.trim(),
            timestamp: new Date()
        };
        this.addMessage(userMessage);

        // 어시스턴트 메시지 생성 (로딩 상태)
        const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true
        };
        this.addMessage(assistantMessage);
        this.currentStreamingMessageId = assistantMessage.id;

        this.setState({ status: 'loading', error: null });

        try {
            // SSE 엔드포인트 호출
            const url = `${this.endpoint}/chat/stream?message=${encodeURIComponent(message)}&context=${context}`;
            const eventSource = new EventSource(url);

            let isFinished = false;

            eventSource.onmessage = (event) => {
                try {
                    console.log('📥 SSE message received:', event.data);
                    const chunk: StreamChunk = JSON.parse(event.data);
                    console.log('📦 Parsed chunk:', chunk);

                    if (chunk.type === 'done') {
                        isFinished = true;
                    }

                    this.handleStreamChunk(chunk, assistantMessage.id);
                } catch (e) {
                    console.error('❌ Failed to parse stream chunk:', e, event.data);
                }
            };

            eventSource.onerror = (error) => {
                eventSource.close();

                // 이미 완료되었거나 의도적으로 종료된 경우 에러 처리 하지 않음
                if (isFinished) {
                    this.currentStreamingMessageId = null;
                    return;
                }

                // 현재 메시지에 내용이 있는지 확인
                const currentMsg = this.state.messages.find(m => m.id === assistantMessage.id);
                const hasContent = currentMsg && currentMsg.content && currentMsg.content.length > 0;

                if (hasContent) {
                    // 내용이 있으면 성공으로 처리 (연결이 끊겼지만 데이터는 받음)
                    console.warn('⚠️ Stream connection closed but content received. Treating as success.');
                    this.updateMessage(assistantMessage.id, {
                        isStreaming: false
                    });
                    this.setState({ status: 'success' });
                } else {
                    // 내용이 없으면 진짜 에러
                    this.updateMessage(assistantMessage.id, {
                        content: '❌ 연결 오류가 발생했습니다.',
                        isStreaming: false
                    });
                    this.setState({ status: 'error', error: 'Connection error' });
                }

                this.currentStreamingMessageId = null;
            };

            // 완료 시 정리
            eventSource.addEventListener('done', () => {
                isFinished = true;
                eventSource.close();
                this.updateMessage(assistantMessage.id, {
                    isStreaming: false
                });
                this.setState({ status: 'success' });
                this.currentStreamingMessageId = null;
            });
        } catch (error) {
            this.updateMessage(assistantMessage.id, {
                content: `❌ Error: ${error instanceof Error ? error.message : String(error)}`,
                isStreaming: false
            });
            this.setState({
                status: 'error',
                error: error instanceof Error ? error.message : String(error)
            });
            this.currentStreamingMessageId = null;
        }
    }

    private async executeNonStreaming(query: string, context: string, messageId: string): Promise<void> {
        const res = await fetch(this.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, context })
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(errText);
        }

        const data: ApiResponse = await res.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // UI가 있으면 UI 트리 추가, 없으면 텍스트만
        const content = data.generated_spec
            ? '✅ UI가 생성되었습니다!'
            : '응답을 생성했습니다.';

        this.updateMessage(messageId, {
            content,
            uiTree: data.generated_spec || undefined,
            isStreaming: false
        });

        this.setState({ status: 'success' });
    }

    private async executeStreaming(query: string, context: string, messageId: string): Promise<void> {
        const res = await fetch(this.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({ query, context })
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(errText);
        }

        // 스트리밍 응답 처리
        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        if (!reader) {
            // 스트리밍을 지원하지 않으면 일반 응답으로 처리
            return this.executeNonStreaming(query, context, messageId);
        }

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const chunk: StreamChunk = JSON.parse(line.slice(6));
                        await this.handleStreamChunk(chunk, messageId);
                    } catch (e) {
                        // JSON 파싱 실패 시 무시
                        console.warn('Failed to parse stream chunk:', e);
                    }
                }
            }
        }

        // 남은 버퍼 처리
        if (buffer.startsWith('data: ')) {
            try {
                const chunk: StreamChunk = JSON.parse(buffer.slice(6));
                await this.handleStreamChunk(chunk, messageId);
            } catch (e) {
                console.warn('Failed to parse final stream chunk:', e);
            }
        }

        this.updateMessage(messageId, {
            isStreaming: false
        });
        this.setState({ status: 'success' });
    }

    private handleStreamChunk(chunk: StreamChunk, messageId: string): void {
        const currentMessage = this.state.messages.find(m => m.id === messageId);
        if (!currentMessage) return;

        switch (chunk.type) {
            case 'text':
                if (chunk.content) {
                    const newContent = currentMessage.content + chunk.content;
                    this.updateMessage(messageId, {
                        content: newContent
                    });
                }
                break;

            case 'ui':
                if (chunk.uiTree) {
                    this.updateMessage(messageId, {
                        uiTree: chunk.uiTree,
                        content: currentMessage.content || '✅ UI가 생성되었습니다!'
                    });
                }
                break;

            case 'error':
                this.updateMessage(messageId, {
                    content: `❌ Error: ${chunk.error || 'Unknown error'}`,
                    isStreaming: false
                });
                this.setState({
                    status: 'error',
                    error: chunk.error || 'Unknown error'
                });
                this.currentStreamingMessageId = null;
                break;

            case 'done':
                this.updateMessage(messageId, {
                    isStreaming: false
                });
                this.currentStreamingMessageId = null;
                break;
        }
    }

    async connect(endpoint: string, ttlContent: string): Promise<ConnectResult> {
        this.setState({ connectionStatus: 'connecting' });

        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ttl_content: ttlContent,
                    base_iri: "http://myapp.com/ui/"
                })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText);
            }

            const data: ConnectResponse = await res.json();

            this.isConnected = true;
            this.setState({
                connectionStatus: 'connected'
            });

            return {
                success: true,
                message: data.message,
                nodeCount: data.node_count
            };
        } catch (error) {
            this.isConnected = false;
            this.setState({
                connectionStatus: 'error'
            });

            return {
                success: false,
                message: error instanceof Error ? error.message : String(error)
            };
        }
    }

    getMessages(): ChatMessage[] {
        return this.state.messages;
    }

    clearMessages(): void {
        this.setState({ messages: [] });
    }

    restoreConnection(): void {
        this.isConnected = true;
        this.setState({
            connectionStatus: 'connected'
        });
    }
}

export { default as UIRenderer } from './UIRenderer.svelte';
export { generateTTLFromDesignSystem } from './ttl-generator';
export type { ComponentMetadata } from './ttl-generator';