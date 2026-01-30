/**
 * Component Scanner
 * 
 * Scans a directory for Svelte components and extracts metadata
 */

import type {
  ComponentInfo,
  ExtractedProp,
  ScanOptions,
  ScanResult,
  ScanError,
  ComponentMetadata
} from '../types';
import { createDefaultMetadata, mergeMetadata, propsToSchema } from '../types/utils';

/**
 * Scan a directory for Svelte components
 * 
 * @example
 * ```ts
 * const result = await scanComponents({
 *   directory: './src/lib/components',
 *   extensions: ['.svelte'],
 *   recursive: true
 * });
 * ```
 */
export async function scanComponents(options: ScanOptions): Promise<ScanResult> {
  const {
    directory,
    extensions = ['.svelte'],
    recursive = true,
    existingMetadata = {}
  } = options;
  
  const components: ComponentInfo[] = [];
  const metadata: Record<string, ComponentMetadata> = {};
  const errors: ScanError[] = [];
  
  try {
    // Browser environment - need file list from user
    if (typeof window !== 'undefined') {
      throw new Error('scanComponents requires Node.js environment. Use scanFromFileList for browser.');
    }
    
    // Node.js environment
    const fs = await import('fs/promises');
    const path = await import('path');
    
    const files = await scanDirectory(directory, extensions, recursive, fs, path);
    
    for (const file of files) {
      try {
        const content = await fs.readFile(file, 'utf-8');
        const info = extractMetadataFromComponent(content, file, path);
        components.push(info);
        
        // Generate or merge metadata
        const defaultMeta = createDefaultMetadata(info.name);
        defaultMeta.propSchema = propsToSchema(info.props);
        
        if (existingMetadata[info.name]) {
          metadata[info.name] = mergeMetadata(existingMetadata[info.name], defaultMeta);
        } else {
          metadata[info.name] = defaultMeta;
        }
      } catch (err) {
        errors.push({
          file,
          message: err instanceof Error ? err.message : String(err)
        });
      }
    }
  } catch (err) {
    errors.push({
      file: directory,
      message: err instanceof Error ? err.message : String(err)
    });
  }
  
  return {
    components,
    metadata,
    scannedAt: new Date(),
    directory,
    errors
  };
}

/**
 * Scan directory for files with specific extensions
 */
export async function scanDirectory(
  dir: string,
  extensions: string[],
  recursive: boolean,
  fs: typeof import('fs/promises'),
  path: typeof import('path')
): Promise<string[]> {
  const files: string[] = [];
  
  const entries = await fs.readdir(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    
    if (entry.isDirectory() && recursive) {
      const subFiles = await scanDirectory(fullPath, extensions, recursive, fs, path);
      files.push(...subFiles);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (extensions.includes(ext)) {
        files.push(fullPath);
      }
    }
  }
  
  return files;
}

/**
 * Extract metadata from a Svelte component file content
 */
export function extractMetadataFromComponent(
  content: string,
  filePath: string,
  path?: typeof import('path')
): ComponentInfo {
  const filename = path ? path.basename(filePath) : filePath.split('/').pop() ?? filePath;
  const name = filename.replace(/\.svelte$/, '');
  
  // Check for script and style blocks
  const hasScript = /<script[\s\S]*?>[\s\S]*?<\/script>/i.test(content);
  const hasStyle = /<style[\s\S]*?>[\s\S]*?<\/style>/i.test(content);
  
  // Extract props from script block
  const props = extractProps(content);
  
  return {
    name,
    path: filePath,
    filename,
    props,
    hasScript,
    hasStyle,
    rawContent: content
  };
}

/**
 * Extract props from Svelte component script
 */
function extractProps(content: string): ExtractedProp[] {
  const props: ExtractedProp[] = [];
  
  // Match script block
  const scriptMatch = content.match(/<script[^>]*>([\s\S]*?)<\/script>/i);
  if (!scriptMatch) return props;
  
  const scriptContent = scriptMatch[1];
  
  // Match "export let propName: Type = default;"
  const propRegex = /export\s+let\s+(\w+)\s*(?::\s*([^=;]+))?\s*(?:=\s*([^;]+))?;/g;
  
  let match;
  while ((match = propRegex.exec(scriptContent)) !== null) {
    const [, name, type, defaultValue] = match;
    props.push({
      name,
      type: type?.trim() ?? 'unknown',
      defaultValue: defaultValue?.trim(),
      required: !defaultValue
    });
  }
  
  // Also match Svelte 5 $props() syntax
  const propsDestructure = scriptContent.match(/let\s*\{([^}]+)\}\s*=\s*\$props\(/);
  if (propsDestructure) {
    const propsStr = propsDestructure[1];
    const propNames = propsStr.split(',').map(p => p.trim().split('=')[0].split(':')[0].trim());
    for (const propName of propNames) {
      if (propName && !props.find(p => p.name === propName)) {
        props.push({
          name: propName,
          type: 'unknown',
          required: !propsStr.includes(`${propName}=`) && !propsStr.includes(`${propName} =`)
        });
      }
    }
  }
  
  return props;
}

/**
 * Scan from a list of file contents (for browser environment)
 */
export function scanFromFileList(
  files: Array<{ name: string; content: string }>,
  existingMetadata: Record<string, ComponentMetadata> = {}
): ScanResult {
  const components: ComponentInfo[] = [];
  const metadata: Record<string, ComponentMetadata> = {};
  const errors: ScanError[] = [];
  
  for (const file of files) {
    try {
      const info = extractMetadataFromComponent(file.content, file.name);
      components.push(info);
      
      const defaultMeta = createDefaultMetadata(info.name);
      defaultMeta.propSchema = propsToSchema(info.props);
      
      if (existingMetadata[info.name]) {
        metadata[info.name] = mergeMetadata(existingMetadata[info.name], defaultMeta);
      } else {
        metadata[info.name] = defaultMeta;
      }
    } catch (err) {
      errors.push({
        file: file.name,
        message: err instanceof Error ? err.message : String(err)
      });
    }
  }
  
  return {
    components,
    metadata,
    scannedAt: new Date(),
    directory: 'browser',
    errors
  };
}
