/// <reference types="svelte" />

declare module '*.svelte' {
  import { SvelteComponentDev } from 'svelte/internal';
  const instance: typeof SvelteComponentDev;
  export default instance;
}