<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import { marked } from "marked";
  import DOMPurify from "dompurify";
  import {
    OgentRuntime,
    UIRenderer,
    generateTTLFromDesignSystem,
    type ChatMessage,
    type ComponentMetadata,
  } from "@ogen/svelte";
  import {
    designSystem,
    designSystemMetadata as defaultDesignSystemMetadata,
  } from "$lib/ds";

  // Render assistant text as sanitized Markdown. Guarded for SSR (DOMPurify
  // needs a DOM); falls back to escaped plain text on the server.
  const escapeHtml = (s: string): string =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  const renderMarkdown = (text: string): string => {
    if (!browser) return escapeHtml(text);
    const html = marked.parse(text, { async: false }) as string;
    return DOMPurify.sanitize(html);
  };

  // Persistent greeting shown as the first assistant turn.
  const WELCOME_TEXT = "Hi! What can I help you with?";

  let query: string = "";
  let runtime: OgentRuntime | null = null;
  let messages: ChatMessage[] = [];
  let chatContainer: HTMLElement | null = null;
  let connectionStatus: "disconnected" | "connecting" | "connected" | "error" =
    "disconnected";
  let activeMetadata: Record<string, ComponentMetadata> =
    defaultDesignSystemMetadata;

  onMount(() => {
    // Check if design system is already connected to backend
    const connectionKey = "ogen_design_system_hash";

    // Allow Design Studio to override metadata via localStorage
    try {
      const storedMetadata = localStorage.getItem(
        "ogen_design_system_metadata",
      );
      if (storedMetadata) {
        activeMetadata = JSON.parse(storedMetadata);
      }
    } catch (error) {
      console.warn(
        "⚠️ Failed to load design studio metadata, falling back to defaults:",
        error,
      );
    }

    const currentHash = JSON.stringify(activeMetadata);
    const storedHash = localStorage.getItem(connectionKey);

    // 런타임 생성
    runtime = new OgentRuntime("http://localhost:8000", {
      connectEndpoint: "http://localhost:8000/api/connect",
      autoConnect: false, // Disable auto-connect, we'll handle manually
      enableStreaming: true,
    });

    // 상태 구독 (runtime is guaranteed to be non-null here)
    const unsubscribe = runtime.subscribe((state) => {
      connectionStatus = state.connectionStatus;
      // Welcome is a persistent, separately-rendered block (see template), so
      // here we simply mirror the runtime's conversation messages.
      messages = state.messages;
    });

    // Check backend connection status first
    const checkConnectionAndConnect = async () => {
      if (!runtime) {
        console.error("❌ Runtime not initialized");
        return;
      }

      try {
        // Check if backend already has our design system
        const statusResponse = await fetch(
          "http://localhost:8000/api/connect/status",
        );
        const statusData = await statusResponse.json();

        if (statusData.connected && storedHash === currentHash) {
          console.log(
            "✅ Design system already connected to backend, skipping connection",
          );
          // Already connected, no need to reconnect network, but need to update runtime state
          runtime.restoreConnection();
          return;
        }

        // Need to connect (either first time or design system changed)
        console.log("🔄 Connecting design system to backend...");

        const userKnowledgeTTL = generateTTLFromDesignSystem(
          designSystem,
          activeMetadata,
        );

        // Connect to backend
        const forceReconnect = storedHash !== currentHash;
        const result = await runtime!.connect(
          "http://localhost:8000/api/connect",
          userKnowledgeTTL,
          forceReconnect,
        );

        if (result.success) {
          // Save connection hash to avoid reconnection
          localStorage.setItem(connectionKey, currentHash);
          console.log("✅ Design system connected successfully");
        } else {
          console.error("❌ Failed to connect design system:", result.message);
        }
      } catch (error) {
        console.error("❌ Error checking connection status:", error);
        // Fallback: try to connect anyway
        if (runtime) {
          const userKnowledgeTTL = generateTTLFromDesignSystem(
            designSystem,
            activeMetadata,
          );
          const forceReconnect = storedHash !== currentHash;
          await runtime.connect(
            "http://localhost:8000/api/connect",
            userKnowledgeTTL,
            forceReconnect,
          );
        }
      }
    };

    // Execute connection logic
    checkConnectionAndConnect();

    return unsubscribe;
  });

  // Ordered segments for an assistant turn. Falls back to content/uiTree for
  // messages produced before the segment model (e.g. the welcome message).
  type Segment =
    | { type: "text"; text: string }
    | { type: "ui"; uiTree: any };

  const getSegments = (message: ChatMessage): Segment[] => {
    if (message.segments && message.segments.length > 0) {
      return message.segments as Segment[];
    }
    const segs: Segment[] = [];
    if (message.uiTree) segs.push({ type: "ui", uiTree: message.uiTree });
    if (message.content) segs.push({ type: "text", text: message.content });
    return segs;
  };

  const handleSend = async () => {
    if (!query.trim()) return;

    const message = query.trim();
    query = "";

    // 채팅 메시지 전송
    if (runtime) {
      await runtime.sendChatMessage(message);
    } else {
      console.error("❌ Runtime not initialized when trying to send message");
    }

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
      {#if connectionStatus === "connected"}
        <div class="connection-status success">Connected</div>
      {:else if connectionStatus === "connecting"}
        <div class="connection-status connecting">Connecting...</div>
      {:else if connectionStatus === "error"}
        <div class="connection-status error">Connection Failed</div>
      {/if}
    </div>
  </header>

  <main class="chat-container" bind:this={chatContainer}>
    <div class="messages">
      <!-- Persistent greeting (always shown as the first assistant turn) -->
      <div class="message message-assistant">
        <div class="message-avatar">A</div>
        <div class="message-content-wrapper">
          <div class="message-content markdown">{@html renderMarkdown(WELCOME_TEXT)}</div>
        </div>
      </div>

      {#each messages as message (message.id)}
        <div class="message message-{message.role}">
          <!-- One avatar per message/turn -->
          <div class="message-avatar">
            {message.role === "user" ? "U" : "A"}
          </div>
          <div class="message-content-wrapper">
            {#if message.role === "user"}
              <div class="message-content">{message.content}</div>
            {:else}
              {@const segs = getSegments(message)}
              <!-- Assistant: render text/UI segments in arrival order -->
              {#each segs as seg, i (i)}
                {#if seg.type === "text"}
                  {#if seg.text.trim()}
                    <div class="message-content markdown">{@html renderMarkdown(seg.text)}{#if message.isStreaming && i === segs.length - 1}<span class="cursor">▋</span>{/if}</div>
                  {/if}
                {:else if seg.type === "ui"}
                  <div class="message-ui">
                    <UIRenderer
                      node={seg.uiTree}
                      components={designSystem}
                      metadata={activeMetadata}
                    />
                  </div>
                {/if}
              {/each}

              {#if message.isStreaming && segs.length === 0}
                <!-- Waiting feedback: shimmering "Responding…" -->
                <div class="responding" aria-live="polite">Responding…</div>
              {/if}
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </main>

  <footer class="input-area">
    <div class="input-wrapper">
      <form class="input-box" on:submit|preventDefault={handleSend}>
        <input bind:value={query} placeholder="Message Ogen UI..." />
        <button type="submit" disabled={!query.trim()}> ➤ </button>
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
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }

  .message-user .message-content-wrapper {
    align-items: flex-end;
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
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0;
    }
  }

  .message-ui {
    margin-top: 0;
    width: 100%;
  }

  /* Waiting feedback: gray "Responding…" with a wave of color sweeping across */
  .responding {
    font-size: 14px;
    font-weight: 500;
    background: linear-gradient(
      90deg,
      #9aa0a6 0%,
      #9aa0a6 35%,
      #10a37f 50%,
      #9aa0a6 65%,
      #9aa0a6 100%
    );
    background-size: 200% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
    animation: responding-wave 1.4s linear infinite;
  }

  @keyframes responding-wave {
    0% {
      background-position: 100% 0;
    }
    100% {
      background-position: -100% 0;
    }
  }

  /* Markdown-rendered assistant text */
  .markdown :global(p) {
    margin: 0 0 8px;
  }
  .markdown :global(p:last-child) {
    margin-bottom: 0;
  }
  .markdown :global(ul),
  .markdown :global(ol) {
    margin: 4px 0 8px;
    padding-left: 20px;
  }
  .markdown :global(li) {
    margin: 2px 0;
  }
  .markdown :global(code) {
    background: rgba(0, 0, 0, 0.06);
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 0.9em;
  }
  .markdown :global(pre) {
    background: #f0f0f2;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
  }
  .markdown :global(pre code) {
    background: none;
    padding: 0;
  }
  .markdown :global(a) {
    color: #10a37f;
    text-decoration: underline;
  }
  .markdown :global(h1),
  .markdown :global(h2),
  .markdown :global(h3) {
    margin: 8px 0 4px;
    font-size: 1.05em;
  }
  .markdown :global(strong) {
    font-weight: 600;
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
