<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    OgentRuntime, 
    UIRenderer, 
    generateTTLFromDesignSystem,
    type ChatMessage
  } from '@ogen/svelte';
  import { designSystem, designSystemMetadata } from '$lib/ds';

  let query: string = "";
  let runtime: OgentRuntime;
  let messages: ChatMessage[] = [];
  let chatContainer: HTMLElement | null = null;
  let connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error' = 'disconnected';

  onMount(() => {
    // 라이브러리 함수로 TTL 생성 (메타데이터 활용)
    const userKnowledgeTTL = generateTTLFromDesignSystem(designSystem, designSystemMetadata);
    
    // 런타임 생성 및 자동 연결
    runtime = new OgentRuntime('http://localhost:8000', {
      connectEndpoint: 'http://localhost:8000/api/connect',
      ttlContent: userKnowledgeTTL,
      autoConnect: true,
      enableStreaming: true
    });
    
    // 상태 구독
    const unsubscribe = runtime.subscribe(state => {
      messages = state.messages;
      connectionStatus = state.connectionStatus;
      
      // 연결 시 환영 메시지
      if (state.connectionStatus === 'connected' && messages.length === 0) {
        messages.push({
          id: 'welcome',
          role: 'assistant',
          content: '안녕하세요! 무엇을 도와드릴까요?',
          timestamp: new Date()
        });
      }
    });
    
    // 수동 연결도 시도 (autoConnect가 실패했을 경우 대비)
    (async () => {
      if (runtime && runtime.getMessages().length === 0) {
        await runtime.connect('http://localhost:8000/api/connect', userKnowledgeTTL);
      }
    })();
    
    return unsubscribe;
  });

  const handleSend = async () => {
    if (!query.trim()) return;
    
    const message = query.trim();
    query = '';
    
    // 채팅 메시지 전송
    await runtime.sendChatMessage(message);
    
    // 스크롤을 맨 아래로
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
</script>
  
<div class="layout">
  <header>
    <h1>💬 Ogen UI Chat</h1>
    {#if connectionStatus === 'connected'}
      <div class="connection-status success">
        ✅ Knowledge Graph Connected
      </div>
    {:else if connectionStatus === 'connecting'}
      <div class="connection-status connecting">
        🔄 Connecting to Knowledge Graph...
      </div>
    {:else if connectionStatus === 'error'}
      <div class="connection-status error">
        ❌ Connection failed. Please refresh the page.
      </div>
    {/if}
  </header>

  <main class="chat-container" bind:this={chatContainer}>
    <div class="messages">
      {#each messages as message (message.id)}
        <div class="message message-{message.role}">
          <div class="message-header">
            <span class="message-role">
              {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
            </span>
            <span class="message-time">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
          <div class="message-content">
            {message.content}
            {#if message.isStreaming}
              <span class="cursor">▋</span>
            {/if}
          </div>
          {#if message.uiTree}
            <div class="message-ui">
              <UIRenderer 
                node={message.uiTree} 
                components={designSystem} 
              />
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </main>

  <footer class="input-area">
    <div class="input-box">
      <input 
        bind:value={query} 
        placeholder="메시지를 입력하세요..." 
        on:keydown={handleKeyDown}
      />
      <button 
        on:click={handleSend}
        disabled={!query.trim()}
      >
        📤
      </button>
    </div>
  </footer>
</div>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
    background: #f5f5f5;
  }
  
  header {
    padding: 20px 24px;
    background: white;
    border-bottom: 1px solid #e0e0e0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }
  
  header h1 {
    margin: 0 0 12px 0;
    font-size: 24px;
    font-weight: 600;
  }
  
  .connection-status {
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    display: inline-block;
  }
  
  .connection-status.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
  }
  
  .connection-status.connecting {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
  }
  
  .connection-status.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
  }
  
  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    background: #f5f5f5;
  }
  
  .messages {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .message {
    display: flex;
    flex-direction: column;
    max-width: 80%;
    animation: fadeIn 0.3s ease-in;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .message-user {
    align-self: flex-end;
  }
  
  .message-assistant {
    align-self: flex-start;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 12px;
    color: #666;
  }
  
  .message-role {
    font-weight: 600;
  }
  
  .message-time {
    opacity: 0.7;
  }
  
  .message-content {
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.5;
    word-wrap: break-word;
  }
  
  .cursor {
    display: inline-block;
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  .message-user .message-content {
    background: #007bff;
    color: white;
    border-bottom-right-radius: 4px;
  }
  
  .message-assistant .message-content {
    background: white;
    color: #333;
    border: 1px solid #e0e0e0;
    border-bottom-left-radius: 4px;
  }
  
  .message-ui {
    margin-top: 12px;
    padding: 16px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  
  .input-area {
    padding: 20px 24px;
    background: white;
    border-top: 1px solid #e0e0e0;
    box-shadow: 0 -2px 4px rgba(0,0,0,0.05);
  }
  
  .input-box { 
    display: flex; 
    gap: 12px; 
  }
  
  input { 
    flex: 1; 
    padding: 12px 16px;
    border: 1px solid #ddd;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }
  
  input:focus {
    border-color: #007bff;
  }
  
  input:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }
  
  button {
    padding: 12px 24px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 24px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.2s;
    min-width: 60px;
  }
  
  button:hover:not(:disabled) {
    background-color: #0056b3;
  }
  
  button:disabled {
    background-color: #6c757d;
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  .empty { 
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    border: 2px dashed #ccc; 
    padding: 40px; 
    text-align: center; 
    color: #888;
    border-radius: 6px;
    background: white;
  }
</style>