/**
 * TTL Generator
 * 
 * Converts component metadata to TTL (Turtle) format for RDF/ontology
 */

import type { ComponentMetadata, TTLGenerationOptions } from '../types';
import { createDefaultMetadata } from '../types/utils';

/**
 * Generate TTL from metadata map
 * 
 * @example
 * ```ts
 * const ttl = generateTTL(metadata, {
 *   baseIRI: 'http://myapp.com/ui/',
 *   ontologyPrefix: 'http://ogen.ai/ontology/'
 * });
 * ```
 */
export function generateTTL(
  metadata: Record<string, ComponentMetadata>,
  options: TTLGenerationOptions = {}
): string {
  const {
    baseIRI = 'http://myapp.com/ui/',
    ontologyPrefix = 'http://ogen.ai/ontology/',
    includeComments = true,
    prettyPrint = true
  } = options;
  
  const lines: string[] = [];
  const nl = prettyPrint ? '\n' : ' ';
  
  // Prefixes
  lines.push(`@prefix user: <${baseIRI}> .`);
  lines.push(`@prefix ogen: <${ontologyPrefix}> .`);
  lines.push(`@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .`);
  lines.push(`@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .`);
  lines.push(`@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .`);
  lines.push('');
  
  // Generate TTL for each component
  for (const [name, meta] of Object.entries(metadata)) {
    if (includeComments) {
      lines.push(`# ${meta.label}`);
    }
    
    const componentTTL = generateComponentTTL(name, meta, baseIRI, ontologyPrefix);
    lines.push(componentTTL);
    lines.push('');
  }
  
  return lines.join(nl);
}

/**
 * Generate TTL for a component registry.
 *
 * - Includes ONLY components present in registryKeys.
 * - If metadata is missing for a component, uses minimal defaults.
 * - Excludes metadata-only nodes ("red") by design.
 */
export function generateTTLForRegistry(
  registryKeys: string[],
  metadata: Record<string, ComponentMetadata>,
  options: TTLGenerationOptions = {}
): string {
  const {
    baseIRI = 'http://myapp.com/ui/',
    ontologyPrefix = 'http://ogen.ai/ontology/',
    includeComments = true,
    prettyPrint = true
  } = options;

  const lines: string[] = [];
  const nl = prettyPrint ? '\n' : ' ';

  lines.push(`@prefix user: <${baseIRI}> .`);
  lines.push(`@prefix ogen: <${ontologyPrefix}> .`);
  lines.push(`@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .`);
  lines.push(`@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .`);
  lines.push(`@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .`);
  lines.push('');

  for (const name of registryKeys) {
    if (name === 'default') continue;
    const meta = metadata[name] ?? createDefaultMetadata(name);
    if (!meta.propSchema) {
      meta.propSchema = {};
    }
    if (includeComments) {
      lines.push(`# ${meta.label ?? name}`);
    }
    lines.push(generateComponentTTL(name, meta, baseIRI, ontologyPrefix));
    lines.push('');
  }

  return lines.join(nl);
}

/**
 * Generate TTL for a single component
 */
export function generateComponentTTL(
  name: string,
  metadata: ComponentMetadata,
  baseIRI: string = 'http://myapp.com/ui/',
  ontologyPrefix: string = 'http://ogen.ai/ontology/'
): string {
  const lines: string[] = [];
  
  // Component declaration
  lines.push(`user:${name} a ogen:${metadata.category} ;`);
  
  // Basic info
  lines.push(`    rdfs:label "${escapeString(metadata.label)}" ;`);
  lines.push(`    rdfs:comment "${escapeString(metadata.comment)}" ;`);
  
  // Keywords
  if (metadata.keywords && metadata.keywords.length > 0) {
    const keywords = metadata.keywords.map(k => escapeString(k)).join(', ');
    lines.push(`    ogen:keywords "${keywords}" ;`);
  }
  
  // Ontology relations
  if (metadata.hasPart && metadata.hasPart.length > 0) {
    for (const part of metadata.hasPart) {
      lines.push(`    ogen:hasPart user:${part} ;`);
    }
  }
  
  if (metadata.requires && metadata.requires.length > 0) {
    for (const req of metadata.requires) {
      lines.push(`    ogen:requires user:${req} ;`);
    }
  }
  
  if (metadata.conflictsWith && metadata.conflictsWith.length > 0) {
    for (const conflict of metadata.conflictsWith) {
      lines.push(`    ogen:conflictsWith user:${conflict} ;`);
    }
  }
  
  if (metadata.recommends && metadata.recommends.length > 0) {
    for (const rec of metadata.recommends) {
      lines.push(`    ogen:recommends user:${rec} ;`);
    }
  }
  
  if (metadata.dependsOn && metadata.dependsOn.length > 0) {
    for (const dep of metadata.dependsOn) {
      lines.push(`    ogen:dependsOn user:${dep} ;`);
    }
  }
  
  // Property schema as JSON
  if (metadata.propSchema && Object.keys(metadata.propSchema).length > 0) {
    const propsJson = JSON.stringify(metadata.propSchema);
    lines.push(`    ogen:propSchema """${propsJson}"""^^xsd:string ;`);
  }
  
  // Layout
  if (metadata.layoutType) {
    lines.push(`    ogen:layoutType "${metadata.layoutType}" ;`);
  }
  
  if (metadata.flexDirection) {
    lines.push(`    ogen:flexDirection "${metadata.flexDirection}" ;`);
  }
  
  if (metadata.spacing) {
    lines.push(`    ogen:spacing "${metadata.spacing}" ;`);
  }
  
  // Accessibility
  if (metadata.ariaLabel) {
    lines.push(`    ogen:ariaLabel "${escapeString(metadata.ariaLabel)}" ;`);
  }
  
  if (metadata.role) {
    lines.push(`    ogen:role "${metadata.role}" ;`);
  }
  
  // State
  if (metadata.defaultState) {
    lines.push(`    ogen:defaultState "${metadata.defaultState}" ;`);
  }
  
  // Style
  if (metadata.variant) {
    lines.push(`    ogen:variant "${metadata.variant}" ;`);
  }
  
  // Validation rules as JSON
  if (metadata.validationRules && Object.keys(metadata.validationRules).length > 0) {
    const rulesJson = JSON.stringify(metadata.validationRules);
    lines.push(`    ogen:validationRules """${rulesJson}"""^^xsd:string ;`);
  }
  
  // Close the statement (replace last ; with .)
  const lastLine = lines[lines.length - 1];
  lines[lines.length - 1] = lastLine.replace(/\s*;$/, ' .');
  
  return lines.join('\n');
}

/**
 * Serialize metadata to TTL string (alias for generateTTL)
 */
export function serializeToTTL(
  metadata: Record<string, ComponentMetadata>,
  options?: TTLGenerationOptions
): string {
  return generateTTL(metadata, options);
}

/**
 * Escape special characters in string for TTL
 */
function escapeString(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t');
}

/**
 * Parse TTL back to metadata (basic parser)
 * Note: This is a simplified parser for our specific TTL format
 */
export function parseTTL(ttl: string): Record<string, Partial<ComponentMetadata>> {
  const metadata: Record<string, Partial<ComponentMetadata>> = {};
  
  // Match component blocks
  const componentRegex = /user:(\w+)\s+a\s+ogen:(\w+)\s*;([^.]+)\./g;
  
  let match;
  while ((match = componentRegex.exec(ttl)) !== null) {
    const [, name, category, properties] = match;
    
    const meta: Partial<ComponentMetadata> = {
      type: name,
      category: category as ComponentMetadata['category']
    };
    
    // Extract label
    const labelMatch = properties.match(/rdfs:label\s+"([^"]+)"/);
    if (labelMatch) meta.label = labelMatch[1];
    
    // Extract comment
    const commentMatch = properties.match(/rdfs:comment\s+"([^"]+)"/);
    if (commentMatch) meta.comment = commentMatch[1];
    
    // Extract keywords
    const keywordsMatch = properties.match(/ogen:keywords\s+"([^"]+)"/);
    if (keywordsMatch) {
      meta.keywords = keywordsMatch[1].split(',').map(k => k.trim());
    }
    
    metadata[name] = meta;
  }
  
  return metadata;
}
