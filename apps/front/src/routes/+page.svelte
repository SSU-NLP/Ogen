<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    OgentRuntime, 
    UIRenderer, 
    generateTTLFromDesignSystem,
    type ChatMessage
  } from '@ogen/svelte';
  import { designSystem, designSystemMetadata as defaultDesignSystemMetadata } from '$lib/ds';

  let query: string = "";
  let runtime: OgentRuntime | null = null;
  let messages: ChatMessage[] = [];
  let chatContainer: HTMLElement | null = null;
  let connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error' = 'disconnected';
  let loadingUIMessages: Set<string> = new Set();

  onMount(() => {
    // Check if design system is already connected to backend
    const connectionKey = 'ogen_design_system_hash';

    // Allow Design Studio to override metadata via localStorage
    let activeMetadata = defaultDesignSystemMetadata;
    try {
      const storedMetadata = localStorage.getItem('ogen_design_system_metadata');
      if (storedMetadata) {
        activeMetadata = JSON.parse(storedMetadata);
      }
    } catch (error) {
      console.warn('⚠️ Failed to load design studio metadata, falling back to defaults:', error);
    }

    const currentHash = JSON.stringify(activeMetadata);
    const storedHash = localStorage.getItem(connectionKey);
    
    // 런타임 생성
    runtime = new OgentRuntime('http://localhost:8000', {
      connectEndpoint: 'http://localhost:8000/api/connect',
      autoConnect: false, // Disable auto-connect, we'll handle manually
      enableStreaming: true
    });
    
    // 상태 구독 (runtime is guaranteed to be non-null here)
    const unsubscribe = runtime.subscribe(state => {
      messages = state.messages;
      connectionStatus = state.connectionStatus;
      
      // Track UI loading states
      loadingUIMessages = new Set(
        state.messages
          .filter(m => m.role === 'assistant' && m.isStreaming && !m.uiTree)
          .map(m => m.id)
      );
      
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
    
    // Check backend connection status first
    const checkConnectionAndConnect = async () => {
      if (!runtime) {
        console.error('❌ Runtime not initialized');
        return;
      }
      
      try {
        // Check if backend already has our design system
        const statusResponse = await fetch('http://localhost:8000/api/connect/status');
        const statusData = await statusResponse.json();
        
        if (statusData.connected && storedHash === currentHash) {
          console.log('✅ Design system already connected to backend, skipping connection');
          // Already connected, no need to reconnect network, but need to update runtime state
          runtime.restoreConnection();
          return;
        }
        
        // Need to connect (either first time or design system changed)
        console.log('🔄 Connecting design system to backend...');
        
        // 라이브러리 함수로 TTL 생성 (메타데이터 활용)
         const userKnowledgeTTL = generateTTLFromDesignSystem(designSystem, activeMetadata);
        
        // Connect to backend
         const forceReconnect = storedHash !== currentHash;
         const result = await runtime!.connect('http://localhost:8000/api/connect', userKnowledgeTTL, forceReconnect);
        
        if (result.success) {
          // Save connection hash to avoid reconnection
          localStorage.setItem(connectionKey, currentHash);
          console.log('✅ Design system connected successfully');
        } else {
          console.error('❌ Failed to connect design system:', result.message);
        }
      } catch (error) {
        console.error('❌ Error checking connection status:', error);
        // Fallback: try to connect anyway
        if (runtime) {
           const userKnowledgeTTL = generateTTLFromDesignSystem(designSystem, activeMetadata);
           const forceReconnect = storedHash !== currentHash;
           await runtime.connect('http://localhost:8000/api/connect', userKnowledgeTTL, forceReconnect);
         }
       }
     };
    
    // Execute connection logic
    checkConnectionAndConnect();
    
    return unsubscribe;
  });

  // Helper function to filter assistant message content
  const getFilteredContent = (message: ChatMessage): string => {
    if (message.role !== 'assistant') return message.content;
    
    // If UI tree exists, show only UI-related message
    if (message.uiTree) {
      return '✅ UI가 생성되었습니다!';
    }
    
    // Filter out unwanted content patterns
    let content = message.content;
    
    // Remove JSON-like content, debug info, etc.
    content = content.replace(/\{[^}]*\}/g, ''); // Remove JSON objects
    content = content.replace(/```[\s\S]*?```/g, ''); // Remove code blocks
    content = content.replace(/`[^`]*`/g, ''); // Remove inline code
    content = content.replace(/🔄|⚡|📝|🎯|🔍|📊|🎨|💡|🚀/g, ''); // Remove emoji indicators
    
    // Clean up extra whitespace
    content = content.replace(/\s+/g, ' ').trim();
    
    // Return cleaned content or default message
    return content || 'UI를 생성 중입니다...';
  };

  const handleSend = async () => {
    if (!query.trim()) return;
    
    const message = query.trim();
    query = '';
    
    // 채팅 메시지 전송
    if (runtime) {
      await runtime.sendChatMessage(message);
    } else {
      console.error('❌ Runtime not initialized when trying to send message');
    }
    
    // 스크롤을 맨 아래로
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  };

  
</script>
  
<div class="layout">
  <header>
    <div class="header-content">
      <h1>Ogen UI Chat</h1>
      {#if connectionStatus === 'connected'}
        <div class="connection-status success">
          Connected
        </div>
      {:else if connectionStatus === 'connecting'}
        <div class="connection-status connecting">
          Connecting...
        </div>
      {:else if connectionStatus === 'error'}
        <div class="connection-status error">
          Connection Failed
        </div>
      {/if}
    </div>
  </header>

  <main class="chat-container" bind:this={chatContainer}>
    <div class="messages">
{#each messages as message (message.id)}
        <div class="message message-{message.role}">
          <div class="message-avatar">
            {message.role === 'user' ? 'U' : 'A'}
          </div>
          <div class="message-content-wrapper">
            <div class="message-content">
              {#if message.role === 'assistant'}
                {getFilteredContent(message)}
              {:else}
                {message.content}
              {/if}
              {#if message.isStreaming && !message.uiTree}
                <span class="cursor">▋</span>
              {/if}
            </div>
            
            {#if message.role === 'assistant' && loadingUIMessages.has(message.id) && !message.uiTree}
              <!-- Skeleton UI while loading -->
              <div class="message-ui skeleton">
                <div class="skeleton-header">
                  <div class="skeleton-line skeleton-title"></div>
                  <div class="skeleton-line skeleton-subtitle"></div>
                </div>
                <div class="skeleton-content">
                  <div class="skeleton-line"></div>
                  <div class="skeleton-line"></div>
                  <div class="skeleton-line skeleton-short"></div>
                </div>
                <div class="skeleton-actions">
                  <div class="skeleton-button"></div>
                  <div class="skeleton-button"></div>
                </div>
              </div>
            {:else if message.uiTree}
              <div class="message-ui">
                <UIRenderer 
                  node={message.uiTree} 
                  components={designSystem} 
                />
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </main>

  <footer class="input-area">
    <div class="input-wrapper">
      <form class="input-box" on:submit|preventDefault={handleSend}>
        <input 
          bind:value={query} 
          placeholder="Message Ogen UI..." 
        />
        <button 
          type="submit"
          disabled={!query.trim()}
        >
          ➤
        </button>
      </form>
    </div>
  </footer>
</div>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #f7f7f8;
  }
  
  header {
    padding: 12px 0;
    background: white;
    border-bottom: 1px solid #e5e5e5;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    flex-shrink: 0;
  }
  
  .header-content {
    max-width: 768px;
    margin: 0 auto;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  header h1 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #202123;
  }
  
  .connection-status {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    display: inline-block;
    font-weight: 500;
  }
  
  .connection-status.success {
    background-color: #10a37f;
    color: white;
  }
  
  .connection-status.connecting {
    background-color: #f4a460;
    color: white;
  }
  
  .connection-status.error {
    background-color: #ef4444;
    color: white;
  }
  
  .chat-container {
    flex: 1;
    overflow-y: auto;
    background: #f7f7f8;
  }
  
  .messages {
    max-width: 768px;
    margin: 0 auto;
    padding: 24px 16px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  
  .message {
    display: flex;
    gap: 16px;
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
    flex-direction: row-reverse;
  }
  
  .message-assistant {
    flex-direction: row;
  }
  
  .message-avatar {
    width: 30px;
    height: 30px;
    border-radius: 2px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
  }
  
  .message-user .message-avatar {
    background: #19c37d;
    color: white;
  }
  
  .message-assistant .message-avatar {
    background: #ab68ff;
    color: white;
  }
  
  .message-content-wrapper {
    flex: 1;
    max-width: 100%;
  }
  
  .message-content {
    background: white;
    color: #202123;
    padding: 12px 16px;
    border-radius: 6px;
    line-height: 1.75;
    word-wrap: break-word;
    font-size: 14px;
  }
  
  .message-user .message-content {
    background: #19c37d;
    color: white;
  }
  
  .message-assistant .message-content {
    background: transparent;
    border: none;
    padding: 0;
  }
  
  .cursor {
    display: inline-block;
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  .message-ui {
    margin-top: 12px;
  }
  
  .skeleton {
    position: relative;
    overflow: hidden;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
  }
  
  .skeleton::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.8),
      transparent
    );
    animation: skeleton-loading 1.5s infinite;
  }
  
  @keyframes skeleton-loading {
    0% { left: -100%; }
    100% { left: 100%; }
  }
  
  .skeleton-header {
    margin-bottom: 16px;
  }
  
  .skeleton-content {
    margin-bottom: 16px;
  }
  
  .skeleton-actions {
    display: flex;
    gap: 8px;
  }
  
  .skeleton-line {
    height: 12px;
    background: #e9ecef;
    border-radius: 4px;
    margin-bottom: 8px;
  }
  
  .skeleton-title {
    height: 20px;
    width: 60%;
    background: #dee2e6;
  }
  
  .skeleton-subtitle {
    height: 14px;
    width: 40%;
    background: #e9ecef;
  }
  
  .skeleton-short {
    width: 30%;
  }
  
  .skeleton-button {
    height: 32px;
    width: 80px;
    background: #e0e0e0;
    border-radius: 16px;
  }
  
  .input-area {
    padding: 24px 16px;
    background: white;
    border-top: 1px solid #e5e5e5;
    flex-shrink: 0;
  }
  
  .input-wrapper {
    max-width: 768px;
    margin: 0 auto;
  }
  
  .input-box { 
    display: flex; 
    gap: 12px;
    align-items: flex-end;
    background: #f7f7f8;
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    padding: 12px 16px;
    transition: border-color 0.2s;
  }
  
  .input-box:focus-within {
    border-color: #10a37f;
  }
  
  input { 
    flex: 1; 
    padding: 8px 0;
    border: none;
    background: transparent;
    font-size: 14px;
    outline: none;
    color: #202123;
    resize: none;
    font-family: inherit;
    line-height: 1.5;
  }
  
  input::placeholder {
    color: #999;
  }
  
  input:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  button {
    padding: 8px 12px;
    background: transparent;
    color: #999;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 32px;
    height: 32px;
  }
  
  button:hover:not(:disabled) {
    background: #10a37f;
    color: white;
  }
  
  button:disabled {
    cursor: not-allowed;
    opacity: 0.4;
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
