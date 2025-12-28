export type UITree = {
    type: string;
    props?: Record<string, any>;
    children?: UITree[];
} | null;

export interface OgenState {
    status: 'idle' | 'loading' | 'error' | 'success';
    tree: UITree;
    error: string | null;
}

export type Listener = (state: OgenState) => void;

interface ApiResponse {
    source_anchor: string;
    reasoning_mode: string;
    generated_spec: UITree;
    error?: string;
}
export class OgenRuntime {
    private endpoint: string;
    private listeners: Listener[] = [];
    private state: OgenState = {
        status: 'idle',
        tree: null, 
        error: null
    };

    constructor(endpoint: string) {
        this.endpoint = endpoint;
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
}

export { default as UIRenderer } from './UIRenderer.svelte';